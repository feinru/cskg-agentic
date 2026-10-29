import json
from datetime import datetime

from modules.config import VALIDATION_REPORTS_DIR

from ..state import ValidationState


def reviewer(state: ValidationState) -> ValidationState:
    results = state.get("validation_results", [])
    if not results:
        print("[Validation] WARNING: No validation results to evaluate.")
        return {"all_done": True}

    total_files = len(results)
    successful_parses = sum(1 for r in results if r["status"] == "success")
    failed_parses = sum(1 for r in results if r["status"] == "failed")
    total_triples = sum(r["total_triples"] for r in results)
    total_subjects = sum(r["validated_subjects"] for r in results)
    total_critical = sum(r["critical_errors_count"] for r in results)
    total_errors = sum(r["errors_count"] for r in results)
    total_warnings = sum(r["warnings_count"] for r in results)

    quality_score = 100.0
    if total_triples > 0:
        quality_score = max(
            0.0, (1.0 - (total_errors + total_critical * 10) / total_triples) * 100
        )
    quality_tier = "EXCELLENT (A)"
    if quality_score < 95.0:
        quality_tier = "GOOD (B)"
    if quality_score < 85.0:
        quality_tier = "FAIR (C)"
    if quality_score < 70.0:
        quality_tier = "POOR (D / FAILED)"

    reports_dir = VALIDATION_REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_readable = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    json_report_file = reports_dir / f"validation_report_{timestamp_filename}.json"

    json_data = {
        "timestamp": timestamp_readable,
        "compliance_score": quality_score,
        "quality_tier": quality_tier,
        "statistics": {
            "total_files": total_files,
            "successful_parses": successful_parses,
            "failed_parses": failed_parses,
            "total_triples": total_triples,
            "total_subjects": total_subjects,
            "critical_errors": total_critical,
            "errors": total_errors,
            "warnings": total_warnings,
        },
        "results": results,
    }
    with open(json_report_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"[Validation] JSON report written to: {json_report_file}")

    return {"all_done": True}


