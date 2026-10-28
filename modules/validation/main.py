import sys
import os
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    if (
        Path.cwd().parent.name in ("agents", "modules")
        and Path.cwd().name == "validation"
    ):
        os.chdir(parent_dir)
    from modules.validation.graph import graph
else:
    from .graph import graph


def run_validation():
    print("[Validation] Cybersecurity KG Quality Assurance Pipeline\n")
    result = graph.invoke(
        {
            "validation_plan": [],
            "current_task": {},
            "validation_results": [],
            "all_done": False,
            "summary": "",
        }
    )
    print("\n[Validation] Semantic Quality Assurance Summary")
    validation_results = result.get("validation_results", [])
    success = [r for r in validation_results if r.get("status") == "success"]
    failed = [r for r in validation_results if r.get("status") != "success"]
    for r in validation_results:
        icon = "[OK]" if r.get("status") == "success" else "[FAIL]"
        print(f"\n{icon} {r['file_name'].upper()}")
        print(f"   File Path     : {r.get('file_path')}")
        print(f"   Parse Status  : {r['status'].upper()}")
        print(f"   Total Triples : {r.get('total_triples', 0):,}")
        print(f"   Total Subjects: {r.get('validated_subjects', 0):,}")
        print(
            f"   Errors Count  : {r.get('errors_count', 0) + r.get('critical_errors_count', 0)}"
        )
        print(f"   Warnings Count: {r.get('warnings_count', 0)}")
        if r.get("error_detail"):
            print(f"   Error Detail  : {r['error_detail']}")
    print(f"\nGraphs Verified Successfully: {len(success)} files")
    print(f"Graphs Failed Verification  : {len(failed)} files")
    total_errors = sum(
        (
            r.get("errors_count", 0) + r.get("critical_errors_count", 0)
            for r in validation_results
        )
    )
    total_warnings = sum((r.get("warnings_count", 0) for r in validation_results))
    print(f"Total Findings: {total_errors} Errors, {total_warnings} Warnings")
    if result.get("summary"):
        print(f"Summary : {result['summary']}")


if __name__ == "__main__":
    run_validation()
