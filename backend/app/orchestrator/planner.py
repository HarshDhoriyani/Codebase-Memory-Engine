from dataclasses import dataclass, field
from .classifier import Intent, IntentType


@dataclass
class QueryPlan:
    intent: Intent

    # which stores to query
    use_graph:   bool = False
    use_vectors: bool = False
    use_git:     bool = False

    # graph query parameters
    graph_queries: list[str] = field(default_factory=list)
    graph_params:  dict = field(default_factory=dict)

    # vector search parameters
    vector_query:  str = ""
    vector_limit:  int = 8
    min_score:     float = 0.35

    # git parameters
    git_function:  str = ""


def plan(intent: Intent) -> QueryPlan:
    """
    Given a classified intent, build a concrete query plan.
    Each plan specifies exactly what to query and with what parameters.
    """
    p = QueryPlan(intent=intent)

    if intent.type == IntentType.STRUCTURAL:
        p.use_graph = True
        q = intent.raw_query.lower()

        # complexity question → direct Neo4j query
        if any(kw in q for kw in ["complex", "complexity", "most complex"]):
            p.graph_queries = ["most_complex"]

        # most called question
        elif any(kw in q for kw in ["most called", "called most", "popular"]):
            p.graph_queries = ["most_called"]

        # most changed question
        elif any(kw in q for kw in ["most changed", "changed most", "modified"]):
            p.graph_queries = ["most_changed"]

        # specific function question
        elif intent.function_name:
            p.graph_queries = ["calls", "called_by", "complexity"]
            p.graph_params  = {"name": intent.function_name}

        else:
            p.graph_queries = ["most_complex", "most_called"]

    elif intent.type == IntentType.SEMANTIC:
        p.use_vectors = True
        p.vector_query = intent.raw_query
        p.vector_limit = 8

    elif intent.type == IntentType.HISTORICAL:
        p.use_graph = True
        p.use_git   = True
        if intent.function_name:
            p.graph_queries = ["history"]
            p.graph_params  = {"name": intent.function_name}
            p.git_function  = intent.function_name
        else:
            p.graph_queries = ["most_changed"]

    elif intent.type == IntentType.HYBRID:
        p.use_graph   = True
        p.use_vectors = True
        p.vector_query = intent.raw_query
        if intent.function_name:
            p.graph_queries = ["calls", "called_by"]
            p.graph_params  = {"name": intent.function_name}

    elif intent.type == IntentType.FULL:
        p.use_graph   = True
        p.use_vectors = True
        p.use_git     = True
        p.vector_query = intent.raw_query
        if intent.function_name:
            p.graph_queries = ["calls", "called_by", "history"]
            p.graph_params  = {"name": intent.function_name}
            p.git_function  = intent.function_name
        else:
            p.graph_queries = ["most_changed", "most_called"]

    return p