import os
import sys
from pathlib import Path
import requests

parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from modules.config import VIRTUOSO_HOST, VIRTUOSO_SPARQL as SPARQL_ENDPOINT


def query(sparql: str, description: str) -> bool:
    print(f"\n[{description}]")
    print(f"Query: {sparql[:80]}...")
    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"query": sparql, "format": "application/sparql-results+json"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[FAIL] Error status: {resp.status_code}")
        return False
    bindings = resp.json()["results"]["bindings"]
    for row in bindings[:3]:
        print("->", {k: v["value"] for k, v in row.items()})
    print(f"[OK] {len(bindings)} results returned")
    return True


def main():
    print("[SPARQL] Verification: SEPSES Cyber-KG")
    tests = [
        (
            "SELECT (COUNT(*) AS ?total) WHERE { ?s ?p ?o }",
            "Total triples across all graphs",
        ),
        ("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }", "List named graphs"),
        (
            "SELECT ?cve ?desc WHERE {\n               GRAPH <http://w3id.org/sepses/graph/cve> {\n                 ?cve a <http://w3id.org/sepses/vocab/ref/cve#CVE> ;\n                      <http://w3id.org/sepses/vocab/ref/cve#id> ?desc .\n               }\n             } LIMIT 3",
            "Sample CVE entries",
        ),
        (
            "SELECT ?cwe ?name WHERE {\n               GRAPH <http://w3id.org/sepses/graph/cwe> {\n                 ?cwe a <http://w3id.org/sepses/vocab/ref/cwe#CWE> ;\n                       <http://w3id.org/sepses/vocab/ref/cwe#name> ?name .\n               }\n             } LIMIT 3",
            "Sample CWE entries",
        ),
        (
            "SELECT ?capec ?attck WHERE {\n               VALUES ?g { <http://w3id.org/sepses/graph/capec2attck> <http://w3id.org/sepses/graph/capec_to_attck> }\n               GRAPH ?g {\n                 ?capec <http://w3id.org/sepses/vocab/ref/capec#hasRelatedAttackPattern> ?attck .\n               }\n             } LIMIT 3",
            "Sample CAPEC to ATT&CK links",
        ),
        (
            "SELECT ?icsa ?cve WHERE {\n               VALUES ?g { <http://w3id.org/sepses/graph/icsa2cve> <http://w3id.org/sepses/graph/icsa_to_cve> }\n               GRAPH ?g {\n                 ?icsa <http://w3id.org/sepses/vocab/ref/icsa#hasCVE> ?cve .\n               }\n             } LIMIT 3",
            "Sample ICSA to CVE links",
        ),
    ]
    passed = 0
    for sparql, desc in tests:
        if query(sparql, desc):
            passed += 1
    print(f"\nTests passed: {passed}/{len(tests)}")
    print(f"Endpoint URL : {SPARQL_ENDPOINT}")
    print(f"Web UI       : http://localhost:8890/conductor\n")


if __name__ == "__main__":
    main()
