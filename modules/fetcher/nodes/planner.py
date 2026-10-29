from state import FetcherState

from modules.config import FETCHER_REGISTRY


def planner(state: FetcherState) -> FetcherState:
    print("[Fetcher] Planning to fetch all available sources.")
    plan = list(FETCHER_REGISTRY.keys())
    print(f"[Fetcher] Plan: {plan}")
    return {
        **state,
        "fetch_plan": plan,
        "current_source": plan[0] if plan else "",
        "results": [],
        "all_done": False,
        "summary": "",
    }
