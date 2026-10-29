import subprocess
import sys
from pathlib import Path

import requests

parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from modules.config import (
    GRAPH_BASE,
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
    total_triples = verify_endpoint()
    print("\n[SPARQL] Final Results")
    print(f"Successful : {success} graphs")
    print(f"Failed     : {failed} graphs")
    if total_triples is not None:
        print(f"Total Triples : {total_triples:,}")
    print(f"Endpoint   : {VIRTUOSO_SPARQL}")
    print(f"Web UI     : http://{VIRTUOSO_HOST}:8890/conductor")


if __name__ == "__main__":
    main()

