from dataclasses import dataclass
from enum import Enum
import re


class IntentType(str, Enum):
    STRUCTURAL   = "structural"    # "what calls X", "what does X import"
    SEMANTIC     = "semantic"      # "find functions that validate email"
    HISTORICAL   = "historical"    # "why did X change", "who modified X"
    HYBRID       = "hybrid"        # needs both graph + vectors
    FULL         = "full"          # needs all three stores


@dataclass
class Intent:
    type: IntentType
    function_name: str | None    # extracted entity if present
    module_name: str | None
    confidence: float
    raw_query: str


# keywords that signal each intent type
STRUCTURAL_KEYWORDS = [
    "calls", "called by", "imports", "depends on",
    "what does", "which functions", "call chain",
    "dependency", "uses", "references", "defines",
]

SEMANTIC_KEYWORDS = [
    "find", "search", "similar", "like", "handles",
    "validates", "parses", "processes", "manages",
    "code that", "functions that", "where is",
]

HISTORICAL_KEYWORDS = [
    "why", "changed", "history", "who", "when",
    "modified", "author", "commit", "evolution",
    "how many times", "last change", "refactor",
]

HYBRID_KEYWORDS = [
    "and", "also", "plus", "as well",
    "relate", "connect", "between",
]


def _extract_function_name(query: str) -> str | None:
    """
    Try to extract a function name from a query.
    Most specific patterns first — foo() before 'function foo'
    to avoid matching common verbs like 'call', 'define', 'use'.
    """
    patterns = [
        r"\b(\w+)\(\)",                                           # validate()
        r"[`'](\w+)[`']\s+function",                             # `validate` function
        r"the\s+[`']?(\w+)[`']?\s+(?:function|method|class)",   # the validate function
        r"\bfunction\s+[`']?(\w+)[`']?",                        # function validate
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            # skip common verbs that aren't function names
            name = match.group(1)
            if name.lower() not in {"call", "calls", "use", "define", "get", "return"}:
                return name
    return None


def _score_keywords(query: str, keywords: list[str]) -> float:
    """Score a query against a keyword list — returns 0.0 to 1.0."""
    q = query.lower()
    matches = sum(1 for kw in keywords if kw in q)
    return min(matches / 2, 1.0)   # 2 matches = confidence 1.0


def classify(query: str) -> Intent:
    """
    Classify a natural language query into an IntentType.
    Returns an Intent with the type, confidence, and any extracted entities.
    """
    q = query.lower().strip()

    struct_score  = _score_keywords(q, STRUCTURAL_KEYWORDS)
    sem_score     = _score_keywords(q, SEMANTIC_KEYWORDS)
    hist_score    = _score_keywords(q, HISTORICAL_KEYWORDS)

    fn_name = _extract_function_name(query)

    # determine intent based on scores
    scores = {
        IntentType.STRUCTURAL: struct_score,
        IntentType.SEMANTIC:   sem_score,
        IntentType.HISTORICAL: hist_score,
    }

    top_type  = max(scores, key=scores.get)
    top_score = scores[top_type]

    # if multiple scores are high → hybrid or full
    high_scores = [k for k, v in scores.items() if v > 0.3]
    if len(high_scores) >= 3:
        intent_type = IntentType.FULL
        confidence  = min(sum(scores.values()) / 2, 1.0)
    elif len(high_scores) == 2:
        intent_type = IntentType.HYBRID
        confidence  = min(sum(scores.values()) / 2, 1.0)
    elif top_score > 0.0:
        intent_type = top_type
        confidence  = top_score
    else:
        # default — treat as semantic search
        intent_type = IntentType.SEMANTIC
        confidence  = 0.3

    return Intent(
        type=intent_type,
        function_name=fn_name,
        module_name=None,
        confidence=confidence,
        raw_query=query,
    )