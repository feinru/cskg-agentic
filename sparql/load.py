import os
import subprocess
import sys
from pathlib import Path
import requests

parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from modules.config import (
    GRAPH_BASE,
    SPARQL_DATA_DIR as TOLOAD_DIR,
    VIRTUOSO_CONTAINER as CONTAINER_NAME,
    VIRTUOSO_HOST,
    VIRTUOSO_SPARQL,
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
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    return (result.returncode, output)


def load_ttl_via_isql(ttl_file: Path, graph_uri: str) -> bool:
    print(f"Loading {ttl_file.name} -> <{graph_uri}>")
    command = f"SPARQL CLEAR GRAPH <{graph_uri}>; SPARQL LOAD <file:///opt/virtuoso-opensource/vsp/toload/{ttl_file.name}> INTO GRAPH <{graph_uri}>;"
    returncode, output = run_isql(command)
    if returncode == 0 and "*** Error" not in output:
        print(f"[OK] Loaded: {ttl_file.name}")
        return True
    else:
        error_lines = [
            l
            for l in output.splitlines()
            if "***" in l or "Error" in l or "error" in l.lower()
        ]
        print(
            f"[FAIL] Error loading {ttl_file.name}: {(chr(10).join(error_lines) if error_lines else output[:200])}"
        )
        return False


def verify_endpoint():
    print("\nVerifying SPARQL endpoint...")
    query = "SELECT (COUNT(*) AS ?total) WHERE { ?s ?p ?o }"
    resp = requests.get(
        VIRTUOSO_SPARQL,
        params={"query": query, "format": "application/sparql-results+json"},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        total = data["results"]["bindings"][0]["total"]["value"]
        print(f"[OK] Endpoint responsive, total triples: {total}")
        return True
    else:
        print(f"[FAIL] Endpoint error status: {resp.status_code}")
        return False


def main():
    print("[SPARQL] Loader: SEPSES Cyber-KG")
    ttl_files = sorted(
        [f for f in TOLOAD_DIR.glob("*.ttl") if not f.name.endswith("_simulated.ttl")]
    )
    if not ttl_files:
        print("ERROR: No .ttl files found in data directory")
        return
    print(f"\nFound {len(ttl_files)} TTL files to load.\n")
    success = 0
    failed = 0
    for ttl_file in ttl_files:
        graph_uri = GRAPH_BASE + ttl_file.stem
        result = load_ttl_via_isql(ttl_file, graph_uri)
        if result:
            success += 1
        else:
            failed += 1
    print(f"\nSuccessfully loaded : {success} files")
    print(f"Failed loads        : {failed} files")
    if success > 0:
        verify_endpoint()
    print(f"\nSPARQL Endpoint : http://localhost:8890/sparql")
    print(f"Web UI          : http://localhost:8890/conductor")
    print(f"Named Graphs    : {GRAPH_BASE}*\n")


if __name__ == "__main__":
    main()
