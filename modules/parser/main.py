import sys
import os
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    if Path.cwd().parent.name in ("agents", "modules") and Path.cwd().name == "parser":
        os.chdir(parent_dir)
    from modules.parser.graph import graph
else:
    from .graph import graph


def run_parser():
    print("[Parser] Cybersecurity KG Pipeline\n")
    result = graph.invoke(
        {
            "parse_plan": [],
            "current_task": {},
            "parsed_results": [],
            "all_done": False,
            "summary": "",
        }
    )
    print("\n[Parser] Final Results")
    success = [r for r in result["parsed_results"] if r.get("status") == "success"]
    failed = [r for r in result["parsed_results"] if r.get("status") == "failed"]
    for r in result["parsed_results"]:
        icon = "[OK]" if r.get("status") == "success" else "[FAIL]"
        print(f"\n{icon} {r['source'].upper()}")
        print(f"   Status     : {r['status']}")
        print(f"   Entities   : {r.get('entities_count', 0)}")
        if r.get("output_file"):
            print(f"   Output     : {r['output_file']}")
        if r.get("error"):
            print(f"   Error      : {r['error']}")
    print(f"\nSuccess : {len(success)} sources")
    print(f"Failed  : {len(failed)} sources")
    if result.get("summary"):
        print(f"Summary : {result['summary']}")


if __name__ == "__main__":
    run_parser()
