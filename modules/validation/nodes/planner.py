from modules.config import LINKING_OUTPUT_DIR, PARSER_OUTPUT_DIR

from ..state import ValidationState


def planner(state: ValidationState) -> ValidationState:
    print("\n[Validation] Analyzing parser and linking outputs for validation plan.")
    parser_output_dir = PARSER_OUTPUT_DIR
    linking_output_dir = LINKING_OUTPUT_DIR
    validation_plan = []
    found_files = []
    if parser_output_dir.exists():
        for file in sorted(parser_output_dir.iterdir()):
            if file.is_file() and file.suffix.lower() == ".ttl":
                found_files.append((file, "parser"))
    if linking_output_dir.exists():
        for file in sorted(linking_output_dir.iterdir()):
            if (
                file.is_file()
                and file.suffix.lower() == ".ttl"
                and "_to_" not in file.name
                and not file.name.endswith("_simulated.ttl")
            ):
                found_files.append((file, "linking"))
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
            print(f"[Validation] Planned: {file_path.name}")
    else:
        print("[Validation] WARNING: No .ttl files found to validate.")
    current_task = validation_plan.pop(0) if validation_plan else {}
    return {
        "validation_plan": validation_plan,
        "current_task": current_task,
        "validation_results": [],
        "all_done": False,
    }
