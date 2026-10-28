from typing import TypedDict


class ParserState(TypedDict, total=False):
    parse_plan: list[dict]
    current_task: dict
    parsed_results: list[dict]
    all_done: bool
    summary: str
