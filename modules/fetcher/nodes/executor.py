from state import FetcherState
from modules.config import FETCHER_REGISTRY


def executor(state: FetcherState) -> FetcherState:
    source = state["current_source"]
    results = list(state["results"])
    plan = state["fetch_plan"]
    print(f"\n[Fetcher] Processing: {source}")
    fetcher_class = FETCHER_REGISTRY.get(source)
    if not fetcher_class:
        result = {
            "source": source,
            "status": "failed",
            "records": 0,
            "file_path": "",
            "error": f"Fetcher for '{source}' not found",
        }
    else:
        fetcher = fetcher_class()
        result = fetcher.run()
    results = [r for r in results if r["source"] != source]
    results.append(result)
    done = {
        r["source"] for r in results if r["status"] in ("success", "cached", "failed")
    }
    remaining = [s for s in plan if s not in done]
    next_source = remaining[0] if remaining else ""
    return {**state, "results": results, "current_source": next_source}
