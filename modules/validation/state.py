from typing import TypedDict


class ValidationState(TypedDict, total=False):
    validation_plan: list[dict]
    current_task: dict
    validation_results: list[dict]
    all_done: bool
