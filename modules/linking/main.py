import sys
import os
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    if Path.cwd().parent.name in ("agents", "modules") and Path.cwd().name == "linking":
        os.chdir(parent_dir)
    from modules.linking.graph import graph
else:
    from .graph import graph


def run_linking():
    print("[Linking] Cybersecurity KG Entity Linking Pipeline\n")
    result = graph.invoke(
        {
            "link_plan": [],
            "current_task": {},
            "linked_results": [],
            "all_done": False,
            "summary": "",
        }
    )
    print("\n[Linking] Final Results")
    linked_results = result.get("linked_results", [])
    success = [r for r in linked_results if r.get("status") == "success"]
    failed = [r for r in linked_results if r.get("status") != "success"]
    for r in linked_results:
        icon = "[OK]" if r.get("status") == "success" else "[FAIL]"
        print(f"\n{icon} {r['link_type'].upper()}")
        print(f"   Predicate : {r.get('predicate', '-')}")
        print(f"   Status    : {r['status']}")
        print(f"   Triples   : {r.get('triples_count', 0)}")
        if r.get("output_file"):
            print(f"   Output    : {r['output_file']}")
        if r.get("error"):
            print(f"   Error     : {r['error']}")
    print(f"\nSuccessful : {len(success)} linking tasks")
    print(f"Failed     : {len(failed)} linking tasks")
    total_triples = sum((r.get("triples_count", 0) for r in linked_results))
    print(f"Total Triples : {total_triples:,}")
    if result.get("summary"):
        print(f"Summary       : {result['summary']}")


if __name__ == "__main__":
    run_linking()
