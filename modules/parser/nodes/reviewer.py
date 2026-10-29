from ..state import ParserState


def reviewer(state: ParserState) -> ParserState:
    print("\n[Parser] Reviewing parsing process.")
    parsed_results = state.get("parsed_results", [])
    total = len(parsed_results)
    success = sum(1 for r in parsed_results if r["status"] == "success")
    failed = total - success
    summary = (
        f"Parsing complete. {success} out of {total} datasets parsed successfully."
    )
    if failed > 0:
        summary += f" Failed: {failed}."
    return {"all_done": True, "summary": summary}
