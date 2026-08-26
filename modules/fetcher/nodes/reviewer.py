from langchain_core.messages import AIMessage
from state import FetcherState

def reviewer(state: FetcherState) -> FetcherState:
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = 2

    results = state.get("results", [])
    
    # Check if there are any failures
    failed_sources = [r["source"] for r in results if r["status"] == "failed"]
    
    print(f"\n[Reviewer] Mengevaluasi hasil... (retry ke-{retry_count})")
    
    if failed_sources and retry_count < MAX_RETRIES:
        verdict = "retry"
        retry_sources = failed_sources
        summary = f"Ditemukan kegagalan pada sumber: {', '.join(failed_sources)}. Memulai retry..."
    else:
        verdict = "done"
        retry_sources = []
        success_count = len([r for r in results if r["status"] in ("success", "cached")])
        total_count = len(results)
        summary = f"Proses selesai. {success_count} dari {total_count} sumber berhasil diproses."

    print(f"[Reviewer] Verdict: {verdict}")
    print(f"[Reviewer] {summary}")

    if verdict == "retry" and retry_sources:
        # Bersihkan results lama untuk source yang akan diretry
        new_results = [r for r in results if r["source"] not in retry_sources]
        
        return {
            **state,
            "fetch_plan": retry_sources,
            "current_source": retry_sources[0],
            "results": new_results,
            "retry_count": retry_count + 1,
            "all_done": False
        }
    else:
        return {
            **state,
            "all_done": True,
            "messages": state["messages"] + [
                AIMessage(content=summary)
            ],
        }