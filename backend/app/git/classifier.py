import re

CATEGORY_KEYWORDS = {
    "bugfix": [
        "fix", "bug", "patch", "resolve", "error",
        "issue", "crash", "broken", "fail", "wrong",
        "incorrect", "regression", "hotfix",
    ],
    "feature": [
        "add", "new", "feature", "implement", "support",
        "create", "introduce", "enable", "allow",
    ],
    "refactor": [
        "refactor", "clean", "restructure", "reorganize",
        "simplify", "rename", "move", "extract", "improve",
        "rewrite", "tidy", "lint",
    ],
    "performance": [
        "perf", "optim", "speed", "fast", "slow",
        "cache", "memory", "latency", "throughput",
    ],
    "docs": [
        "doc", "comment", "readme", "docstring",
        "typo", "spelling", "example", "annotate",
    ],
    "test": [
        "test", "spec", "coverage", "assert",
        "mock", "fixture", "pytest",
    ],
    "chore": [
        "chore", "bump", "update", "upgrade",
        "version", "release", "ci", "cd", "deps",
    ],
}

def classify_commit(message: str) -> str:
    """
    Return the best-matching category for a commit message.
    Falls back to 'chore' if nothing matches.
    """

    msg = message.lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(rf"\b{kw}", msg))
        if score > 0:
            scores[category] = score

    if not scores:
        return "chore"
    return max(scores, key=scores.get) # type: ignore


def classify_commits(messages: list[str]) -> dict[str, int]:

    counts: dict[str, int] = {}
    for msg in messages:
        cat = classify_commit(msg)
        counts[cat] = counts.get(cat, 0) + 1
    return counts

def primary_category(messages: list[str]) -> str:
    if not messages:
        return "unknown"
    counts = classify_commits(messages)
    return max(counts, key=counts.get) # type: ignore