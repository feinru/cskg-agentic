from typing import TypedDict


class LinkingState(TypedDict, total=False):
    link_plan: list[dict]
    current_task: dict
    linked_results: list[dict]
    all_done: bool

