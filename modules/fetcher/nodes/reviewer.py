from state import FetcherState


def reviewer(state: FetcherState) -> FetcherState:
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = 2
    results = state.get("results", [])
    failed_sources = [r["source"] for r in results if r["status"] == "failed"]
    print(f"\n[Fetcher] Evaluating fetch results... (attempt {retry_count + 1})")
    if failed_sources and retry_count < MAX_RETRIES:
        verdict = "retry"
        retry_sources = failed_sources
        summary = (
            f"Failures detected in sources: {', '.join(failed_sources)}. Retrying..."
        )
    else:
        verdict = "done"
        retry_sources = []
        success_count = len(
            [r for r in results if r["status"] in ("success", "cached")]
        )
        total_count = len(results)
        summary = f"Process complete. {success_count} of {total_count} sources processed successfully."
    print(f"[Fetcher] Verdict: {verdict}")
    print(f"[Fetcher] {summary}")
    if verdict == "retry" and retry_sources:
        new_results = [r for r in results if r["source"] not in retry_sources]
        return {
            **state,
            "fetch_plan": retry_sources,
            "current_source": retry_sources[0],
            "results": new_results,
            "retry_count": retry_count + 1,
            "all_done": False,
            "summary": summary,
        }
    else:
        return {**state, "all_done": True, "summary": summary}
