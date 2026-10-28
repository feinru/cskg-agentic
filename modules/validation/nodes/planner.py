import os
from pathlib import Path
from modules.config import PARSER_OUTPUT_DIR, LINKING_OUTPUT_DIR
from ..state import ValidationState


def planner(state: ValidationState) -> ValidationState:
    print("\n[Validation] Analyzing parser and linking outputs for validation...")
    parser_output_dir = PARSER_OUTPUT_DIR
    linking_output_dir = LINKING_OUTPUT_DIR
    validation_plan = []
    found_files = []
    if parser_output_dir.exists():
        for file in sorted(parser_output_dir.iterdir()):
            if file.is_file() and file.suffix.lower() == ".ttl":
                found_files.append((file, "parser"))
                print(f"[Validation] Found base entity graph: {file.name}")
    if linking_output_dir.exists():
        for file in sorted(linking_output_dir.iterdir()):
            if file.is_file() and file.suffix.lower() == ".ttl":
                found_files.append((file, "linking"))
                print(f"[Validation] Found relation graph: {file.name}")
    if found_files:
        for file_path, origin in found_files:
            stem = file_path.stem.lower()
            desc = (
                f"Semantic validation for base entity {stem.upper()}"
                if origin == "parser"
                else f"Semantic validation for relation graph {stem.upper()}"
            )
            task = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "origin": origin,
                "link_type": stem,
                "description": desc,
            }
            validation_plan.append(task)
            print(f"[Validation] Scheduled: {file_path.name}")
    else:
        print("[Validation] WARNING: No .ttl files found to validate.")
    current_task = validation_plan.pop(0) if validation_plan else {}
    if current_task:
        print(f"[Validation] First task queued: {current_task['file_name']}")
    else:
        print("[Validation] No active validation tasks.")
    return {
        "validation_plan": validation_plan,
        "current_task": current_task,
        "validation_results": [],
        "all_done": False,
        "summary": "",
    }
