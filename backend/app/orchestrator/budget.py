CHARS_PER_TOKEN = 4        # rough approximation
MAX_TOKENS      = 6000     # leave 2K for LLM response


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def trim_to_budget(items: list[dict], key: str, max_tokens: int) -> list[dict]:
    """
    Keep as many items as possible within token budget.
    Trims the list from the end (lowest priority items dropped first).
    """
    kept = []
    used = 0
    for item in items:
        text   = str(item.get(key, ""))
        tokens = estimate_tokens(text)
        if used + tokens > max_tokens:
            break
        kept.append(item)
        used += tokens
    return kept


def build_context_string(
    query: str,
    graph_data: dict,
    vector_data: list,
    git_data: list,
    intent_type: str,
) -> str:
    """
    Build the final context string that goes to the LLM.
    Prioritises data based on intent type.
    Stays within MAX_TOKENS.
    """
    sections = []
    budget   = MAX_TOKENS

    # always include the query
    sections.append(f"USER QUESTION: {query}\n")
    budget -= estimate_tokens(sections[-1])

    # --- graph data ---
    if graph_data:
        section = ["CODEBASE STRUCTURE:"]

        if "calls" in graph_data and graph_data["calls"]:
            calls = graph_data["calls"][:10]
            section.append(f"  Calls: {[c['name'] for c in calls]}")

        if "called_by" in graph_data and graph_data["called_by"]:
            callers = graph_data["called_by"][:10]
            section.append(f"  Called by: {[c['name'] for c in callers]}")

        if "most_complex" in graph_data:
            for fn in graph_data["most_complex"][:5]:
                section.append(
                    f"  - {fn['name']} ({fn['file_path']}) "
                    f"complexity={fn['complexity']}"
                )

        if "most_called" in graph_data:
            for fn in graph_data["most_called"][:5]:
                section.append(
                    f"  - {fn['name']} called {fn.get('call_count',0)} times"
                )

        if "history" in graph_data:
            for h in graph_data["history"][:3]:
                section.append(
                    f"  - Changed {h.get('change_count',0)} times, "
                    f"last by {h.get('last_author','unknown')} "
                    f"({h.get('category','unknown')} category)"
                )

        if "most_changed" in graph_data:
            for fn in graph_data["most_changed"][:5]:
                section.append(
                    f"  - {fn['name']} changed "
                    f"{fn.get('change_count',0)} times "
                    f"({fn.get('category','?')})"
                )

        block = "\n".join(section)
        if estimate_tokens(block) < budget:
            sections.append(block)
            budget -= estimate_tokens(block)

    # --- vector data ---
    if vector_data:
        section = ["SEMANTICALLY SIMILAR FUNCTIONS:"]
        for r in vector_data[:6]:
            # skip error dicts from failed Qdrant calls
            if "error" in r or "name" not in r:
                continue
            line = (
                f"  - {r['name']} in {r['file_path']} "
                f"(score={r['score']}, complexity={r.get('complexity',0)})"
            )
            if r.get("docstring"):
                line += f"\n    {r['docstring'][:100]}"
            section.append(line)

        if len(section) > 1:   # only add if we have real results
            block = "\n".join(section)
            if estimate_tokens(block) < budget:
                sections.append(block)
                budget -= estimate_tokens(block)

    sections.append(
        "\nAnswer the user's question using the context above. "
        "Be specific — reference actual function names, file paths, "
        "and line numbers where relevant. "
        "If the context is insufficient, say so clearly."
    )

    return "\n\n".join(sections)