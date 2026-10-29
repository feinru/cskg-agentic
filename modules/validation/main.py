import os
import sys
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
    result = graph.invoke(
        {
            "validation_plan": [],
            "current_task": {},
            "validation_results": [],
            "all_done": False,
        }
    )
    print("\n[Validation] Final Results")
    validation_results = result.get("validation_results", [])
    success = [r for r in validation_results if r.get("status") == "success"]
    failed = [r for r in validation_results if r.get("status") != "success"]
    for r in validation_results:
        icon = "[OK]" if r.get("status") == "success" else "[FAIL]"
        print(f"{icon} {r['link_type'].upper()}")
        print(f"   Status    : {r['status']}")
        print(f"   Triples   : {r.get('total_triples', 0):,}")
        print(f"   Subjects  : {r.get('validated_subjects', 0):,}")
        if r.get("file_path"):
            print(f"   Output    : {r['file_path']}")
        findings_err = r.get("errors_count", 0) + r.get("critical_errors_count", 0)
        findings_warn = r.get("warnings_count", 0)
        print(f"   Findings  : {findings_err} Errors, {findings_warn} Warnings")
        if r.get("error_detail"):
            print(f"   Error     : {r['error_detail']}")
    print(f"Successful : {len(success)} graphs")
    print(f"Failed     : {len(failed)} graphs")
    total_errors = sum(
        r.get("errors_count", 0) + r.get("critical_errors_count", 0)
        for r in validation_results
    )
    total_warnings = sum(r.get("warnings_count", 0) for r in validation_results)
    print(f"Total Findings : {total_errors} Errors, {total_warnings} Warnings")


if __name__ == "__main__":
    run_validation()
