from pathlib import Path
from modules.config import CACHE_DIR
from ..state import ParserState


def planner(state: ParserState) -> ParserState:
    print("[Parser] Analyzing available fetched datasets...")
    cache_dir = CACHE_DIR
    if not cache_dir.exists():
        print(f"[Parser] Error: {cache_dir} directory not found.")
        return state
    parse_plan = []
    for file_path in cache_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".json":
            source = file_path.stem.lower()
            try:
                import json

                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                actual_file = str(file_path)
                parser_type = "json"
                if (
                    isinstance(data, list)
                    and len(data) == 1
                    and isinstance(data[0], dict)
                    and ("file" in data[0])
                ):
                    pointer_file = data[0]["file"].replace("\\", "/")
                    if pointer_file.startswith("cache/"):
                        actual_file = str(cache_dir.parent / pointer_file)
                    else:
                        actual_file = str(cache_dir / Path(pointer_file).name)
                    if actual_file.endswith(".xml"):
                        parser_type = "xml"
            except Exception as e:
                print(f"[Parser] Error reading {file_path.name}: {e}")
                continue
            parse_plan.append(
                {"source": source, "file_path": actual_file, "parser_type": parser_type}
            )
            print(
                f"[Parser] Planned parsing for {source} using {parser_type} parser on {actual_file}."
            )
    if not parse_plan:
        print("[Parser] No supported files found to parse.")
    current_task = parse_plan.pop(0) if parse_plan else {}
    return {"parse_plan": parse_plan, "current_task": current_task}
