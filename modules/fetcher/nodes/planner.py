from state import FetcherState
from config import FETCHER_REGISTRY

def planner(state: FetcherState) -> FetcherState:
    print("\n[Planner] Automatically planning to fetch all available sources.")
    
    plan = list(FETCHER_REGISTRY.keys())
    print(f"[Planner] Plan: {plan}")

    return {
        **state,
        "fetch_plan":     plan,
        "current_source": plan[0] if plan else "",
        "results":        [],
        "all_done":       False,
    }
