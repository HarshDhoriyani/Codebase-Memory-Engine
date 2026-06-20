from dataclasses import dataclass
from .classifier import classify, Intent
from .planner import plan, QueryPlan
from .executor import execute, QueryResults
from .budget import build_context_string


@dataclass
class OrchestratorResult:
    query:        str
    intent_type:  str
    intent_conf:  float
    context:      str         # ready to send to LLM
    graph_data:   dict
    vector_data:  list
    errors:       list
    function_name: str | None


async def process_query(query: str) -> OrchestratorResult:
    """
    Full pipeline:
    query → classify → plan → execute → fuse → context string

    The returned context string is ready to be sent to Claude/GPT.
    """
    # step 1 — classify intent
    intent: Intent = classify(query)

    # step 2 — build query plan
    query_plan: QueryPlan = plan(intent)

    # step 3 — execute queries in parallel
    results: QueryResults = await execute(query_plan)

    # step 4 — build context string within token budget
    context = build_context_string(
        query=query,
        graph_data=results.graph_data,
        vector_data=results.vector_data,
        git_data=results.git_data,
        intent_type=intent.type.value,
    )

    return OrchestratorResult(
        query=query,
        intent_type=intent.type.value,
        intent_conf=round(intent.confidence, 2),
        context=context,
        graph_data=results.graph_data,
        vector_data=results.vector_data,
        errors=results.errors,
        function_name=intent.function_name,
    )