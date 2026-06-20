import asyncio
from dataclasses import dataclass, field
from .planner import QueryPlan
from ..graph import queries as gq
from ..embedder.embedder import embed_query
from ..embedder.qdrant_store import semantic_search


@dataclass
class QueryResults:
    graph_data:  dict  = field(default_factory=dict)
    vector_data: list  = field(default_factory=list)
    git_data:    list  = field(default_factory=list)
    errors:      list  = field(default_factory=list)


def _run_graph_queries(plan: QueryPlan) -> dict:
    """Execute all planned Neo4j queries synchronously."""
    results = {}
    name = plan.graph_params.get("name", "")

    for q in plan.graph_queries:
        try:
            if q == "calls" and name:
                results["calls"] = gq.what_does_function_call(name)
            elif q == "called_by" and name:
                results["called_by"] = gq.what_calls_function(name)
            elif q == "complexity":
                results["most_complex"] = gq.most_complex_functions(5)
            elif q == "most_complex":
                results["most_complex"] = gq.most_complex_functions(10)
            elif q == "most_called":
                results["most_called"] = gq.most_called_functions(10)
            elif q == "most_changed":
                results["most_changed"] = gq.most_changed_functions(10)
            elif q == "history" and name:
                results["history"] = gq.function_git_history(name)
            elif q == "chain" and name:
                results["chain"] = gq.full_call_chain(name, max_depth=4)
        except Exception as e:
            results[f"error_{q}"] = str(e)

    return results


def _run_vector_search(plan: QueryPlan) -> list:
    """Embed the query and search Qdrant."""
    try:
        vec = embed_query(plan.vector_query)
        return semantic_search(
            query_vector=vec,
            limit=plan.vector_limit,
            min_score=plan.min_score,
        )
    except Exception as e:
        return [{"error": str(e)}]


async def execute(plan: QueryPlan) -> QueryResults:
    """
    Execute all queries in the plan concurrently.
    Graph + vector queries run in parallel via asyncio.gather.
    """
    results = QueryResults()

    tasks = []
    task_keys = []

    if plan.use_graph:
        tasks.append(
            asyncio.get_event_loop().run_in_executor(
                None, _run_graph_queries, plan
            )
        )
        task_keys.append("graph")

    if plan.use_vectors:
        tasks.append(
            asyncio.get_event_loop().run_in_executor(
                None, _run_vector_search, plan
            )
        )
        task_keys.append("vectors")

    if tasks:
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        for key, output in zip(task_keys, outputs):
            if isinstance(output, Exception):
                results.errors.append(f"{key}: {str(output)}")
            elif key == "graph":
                results.graph_data = output
            elif key == "vectors":
                results.vector_data = output

    return results