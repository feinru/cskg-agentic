import subprocess
import sys
from pathlib import Path

import requests

parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from modules.config import (
    GRAPH_BASE,
    INFERENCE_RULE_SET,
    ONTOLOGY_DIR,
    ONTOLOGY_GRAPH,
    VIRTUOSO_HOST,
    VIRTUOSO_SPARQL,
)
from modules.config import (
    SPARQL_DATA_DIR as TOLOAD_DIR,
)
from modules.config import (
    VIRTUOSO_CONTAINER as CONTAINER_NAME,
)


def run_isql(command: str) -> tuple[bool, str]:
    result = subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER_NAME,
            "isql",
            "1111",
            "dba",
            "dba",
            f"EXEC={command}",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=600,
    )
    output = result.stdout + result.stderr
    return (result.returncode, output)


def check_loader_error(filename: str) -> str | None:
    code, out = run_isql(
        f"SELECT ll_error FROM DB.DBA.load_list WHERE ll_file LIKE '%/{filename}' AND ll_error IS NOT NULL;"
    )
    if code == 0 and "Rows" in out and "0 Rows" not in out and "NULL" not in out:
        lines = [l.strip() for l in out.splitlines() if l.strip() and not l.startswith("ll_error") and not l.startswith("_") and "Rows" not in l]
        if lines:
            return " ".join(lines)
    return None


def load_ttl_via_isql(ttl_file: Path, graph_uri: str) -> bool:
    stem = ttl_file.stem
    print(f"\n[SPARQL] Processing: {stem}")
    file_size_mb = ttl_file.stat().st_size / (1024 * 1024)
    if file_size_mb > 5.0:
        command = (
            f"SPARQL CLEAR GRAPH <{graph_uri}>; "
            f"DELETE FROM DB.DBA.load_list WHERE ll_file LIKE '%/{ttl_file.name}'; commit work; "
            f"ld_dir('/opt/virtuoso-opensource/vsp/toload', '{ttl_file.name}', '{graph_uri}'); "
            "rdf_loader_run();"
        )
    else:
        command = f"SPARQL CLEAR GRAPH <{graph_uri}>; SPARQL LOAD <file:///opt/virtuoso-opensource/vsp/toload/{ttl_file.name}> INTO GRAPH <{graph_uri}>;"
    returncode, output = run_isql(command)
    if returncode == 0 and "*** Error" not in output:
        ll_err = check_loader_error(ttl_file.name)
        if ll_err:
            print(f"[{stem}] Virtuoso Loader Error: {ll_err}")
            return False
        run_isql(
            f"DB.DBA.RDF_GRAPH_USER_PERMS_SET ('{graph_uri}', 'nobody', 1); checkpoint; commit work;"
        )
        print(f"[{stem}] Loaded -> <{graph_uri}>")
        return True
    if "too large" in output or "39000" in output:
        bulk_command = (
            f"SPARQL CLEAR GRAPH <{graph_uri}>; "
            f"DELETE FROM DB.DBA.load_list WHERE ll_file LIKE '%/{ttl_file.name}'; commit work; "
            f"ld_dir('/opt/virtuoso-opensource/vsp/toload', '{ttl_file.name}', '{graph_uri}'); "
            "rdf_loader_run();"
        )
        returncode, output = run_isql(bulk_command)
        if returncode == 0 and "*** Error" not in output:
            ll_err = check_loader_error(ttl_file.name)
            if ll_err:
                print(f"[{stem}] Virtuoso Loader Error: {ll_err}")
                return False
            run_isql(
                f"DB.DBA.RDF_GRAPH_USER_PERMS_SET ('{graph_uri}', 'nobody', 1); checkpoint; commit work;"
            )
            print(f"[{stem}] Bulk loaded -> <{graph_uri}>")
            return True
    error_lines = [
        l
        for l in output.splitlines()
        if "***" in l or "Error" in l or "error" in l.lower()
    ]
    err_str = chr(10).join(error_lines) if error_lines else output[:200]
    print(f"[{stem}] Error: {err_str}")
    return False


def verify_endpoint() -> int | None:
    query = "SELECT (COUNT(*) AS ?total) WHERE { ?s ?p ?o }"
    try:
        resp = requests.get(
            VIRTUOSO_SPARQL,
            params={"query": query, "format": "application/sparql-results+json"},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return int(data["results"]["bindings"][0]["total"]["value"])
    except (requests.RequestException, KeyError, ValueError, IndexError):
        pass
    return None


def load_ontology_and_rules() -> bool:
    print(f"\n[SPARQL] Loading CSKG Core Ontology & Semantic Rules...")
    onto_dir = TOLOAD_DIR / "ontology"
    source_dir = onto_dir if (onto_dir.exists() and (onto_dir / "ontology.ttl").exists()) else ONTOLOGY_DIR
    target_names = ["core.ttl", "classes.ttl", "relations.ttl", "properties.ttl", "ontology.ttl"]
    onto_files = [source_dir / name for name in target_names if (source_dir / name).exists()]
    if not onto_files:
        print("[SPARQL] No ontology files found to load.")
        return False

    run_isql(f"SPARQL CLEAR GRAPH <{ONTOLOGY_GRAPH}>;")
    for f in onto_files:
        rel_path = f"ontology/{f.name}" if (TOLOAD_DIR / "ontology" / f.name).exists() else f.name
        cmd = f"SPARQL LOAD <file:///opt/virtuoso-opensource/vsp/toload/{rel_path}> INTO GRAPH <{ONTOLOGY_GRAPH}>;"
        code, out = run_isql(cmd)
        if code != 0 or "*** Error" in out:
            print(f"[Ontology] Error loading {f.name}: {out[:120]}")

    run_isql(f"DB.DBA.RDF_GRAPH_USER_PERMS_SET ('{ONTOLOGY_GRAPH}', 'nobody', 1);")
    run_isql(f"rdfs_rule_set ('{INFERENCE_RULE_SET}', '{ONTOLOGY_GRAPH}'); checkpoint; commit work;")
    print(f"[Ontology] Loaded {len(onto_files)} ontology modules into <{ONTOLOGY_GRAPH}> with rule set '{INFERENCE_RULE_SET}'.")
    return True


def main():
    ttl_files = sorted(
        [
            f
            for f in TOLOAD_DIR.glob("*.ttl")
            if not f.name.endswith("_simulated.ttl") and "_to_" not in f.name
        ]
    )
    if not ttl_files:
        print("[SPARQL] ERROR: No .ttl files found in data directory")
        return
    print(f"\n[SPARQL] Found {len(ttl_files)} TTL files to load.")
    success = 0
    failed = 0
    for ttl_file in ttl_files:
        graph_uri = GRAPH_BASE + ttl_file.stem
        result = load_ttl_via_isql(ttl_file, graph_uri)
        if result:
            success += 1
        else:
            failed += 1

    load_ontology_and_rules()

    total_triples = verify_endpoint()
    print("\n[SPARQL] Final Results")
    print(f"Successful : {success} data graphs + ontology")
    print(f"Failed     : {failed} graphs")
    if total_triples is not None:
        print(f"Total Triples : {total_triples:,}")
    print(f"Endpoint   : {VIRTUOSO_SPARQL}")
    print(f"Web UI     : http://{VIRTUOSO_HOST}:8890/conductor")


if __name__ == "__main__":
    main()

