from typing import TypedDict


class FetcherState(TypedDict, total=False):
    fetch_plan: list[str]
    current_source: str
    results: list[dict]
    all_done: bool
    retry_count: int
    summary: str
