from ..state import LinkingState


def reviewer(state: LinkingState) -> LinkingState:
    print("[Linking] Reviewing linking process...")
    linked_results = state.get("linked_results", [])
    total = len(linked_results)
    success = sum((1 for r in linked_results if r.get("status") == "success"))
    failed = total - success
    total_triples = sum((r.get("triples_count", 0) for r in linked_results))
    summary_parts = [
        f"Linking complete. {success} of {total} tasks succeeded.",
        f"Total triples generated: {total_triples}.",
    ]
    if failed > 0:
        failed_types = [
            r["link_type"] for r in linked_results if r.get("status") != "success"
        ]
        summary_parts.append(f"Failed: {failed} tasks ({', '.join(failed_types)}).")
    output_files = [r["output_file"] for r in linked_results if r.get("output_file")]
    if output_files:
        summary_parts.append(f"Output files: {', '.join(output_files)}")
    summary = " ".join(summary_parts)
    print(f"[Linking] {summary}")
    return {"all_done": True, "summary": summary}
