import sys
import os
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    if str(current_file_path.parent) not in sys.path:
        sys.path.insert(0, str(current_file_path.parent))


def run_fetcher():
    from graph import graph

    print("[Fetcher] Cybersecurity KG Pipeline\n")
    result = graph.invoke(
        {
            "fetch_plan": [],
            "current_source": "",
            "results": [],
            "all_done": False,
            "summary": "",
        }
    )
    print("\n[Fetcher] Results Summary")
    success = [r for r in result["results"] if r["status"] in ("success", "cached")]
    failed = [r for r in result["results"] if r["status"] == "failed"]
    for r in result["results"]:
        icon = "[OK]" if r["status"] in ("success", "cached") else "[FAIL]"
        print(f"\n{icon} {r['source'].upper()}")
        print(f"   Status  : {r['status']}")
        print(f"   Records : {r.get('records', 0):,}")
        if r["file_path"]:
            print(f"   File    : {r['file_path']}")
        if r["error"]:
            print(f"   Error   : {r['error']}")
    print(f"\nSuccessful : {len(success)} sources")
    print(f"Failed     : {len(failed)} sources")
    if result.get("summary"):
        print(f"Summary    : {result['summary']}")


if __name__ == "__main__":
    run_fetcher()
