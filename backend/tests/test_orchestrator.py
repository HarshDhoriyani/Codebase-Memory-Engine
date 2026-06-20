from app.orchestrator.classifier import classify, IntentType
from app.orchestrator.planner import plan
from app.orchestrator.budget import estimate_tokens, build_context_string


# ── classifier tests ───────────────────────────────────────

def test_classifies_structural():
    intent = classify("What does the validate function call?")
    assert intent.type == IntentType.STRUCTURAL

def test_classifies_semantic():
    intent = classify("Find functions that handle authentication")
    assert intent.type == IntentType.SEMANTIC

def test_classifies_historical():
    intent = classify("Why did the init function change so many times?")
    assert intent.type == IntentType.HISTORICAL

def test_extracts_function_name():
    intent = classify("What does the validate() function call?")
    assert intent.function_name == "validate"

def test_extracts_function_name_backtick():
    intent = classify("Tell me about the `add_route` function")
    assert intent.function_name == "add_route"

def test_confidence_is_between_0_and_1():
    intent = classify("What calls the router?")
    assert 0.0 <= intent.confidence <= 1.0

def test_unknown_query_defaults_to_semantic():
    intent = classify("hello world")
    assert intent.type == IntentType.SEMANTIC

def test_hybrid_query():
    intent = classify("Find functions similar to validate and what they call")
    assert intent.type in (IntentType.HYBRID, IntentType.FULL, IntentType.SEMANTIC)


# ── planner tests ──────────────────────────────────────────

def test_structural_uses_graph():
    intent = classify("What does validate call?")
    p = plan(intent)
    assert p.use_graph is True
    assert p.use_vectors is False

def test_semantic_uses_vectors():
    intent = classify("Find code that validates email addresses")
    p = plan(intent)
    assert p.use_vectors is True

def test_historical_uses_graph_and_git():
    intent = classify("Why has init changed so many times?")
    p = plan(intent)
    assert p.use_graph is True
    assert p.use_git is True

def test_plan_sets_vector_query():
    intent = classify("Find authentication functions")
    p = plan(intent)
    assert p.vector_query == intent.raw_query


# ── budget tests ───────────────────────────────────────────

def test_estimate_tokens_non_zero():
    assert estimate_tokens("hello world this is a test") > 0

def test_build_context_contains_query():
    ctx = build_context_string(
        query="What does validate call?",
        graph_data={"calls": [{"name": "check", "file_path": "app/utils.py"}]},
        vector_data=[],
        git_data=[],
        intent_type="structural",
    )
    assert "What does validate call?" in ctx

def test_build_context_contains_graph_data():
    ctx = build_context_string(
        query="test query",
        graph_data={"calls": [{"name": "my_function", "file_path": "app.py"}]},
        vector_data=[],
        git_data=[],
        intent_type="structural",
    )
    assert "my_function" in ctx

def test_build_context_contains_vector_data():
    ctx = build_context_string(
        query="find auth code",
        graph_data={},
        vector_data=[{
            "name": "auth_check",
            "file_path": "app/auth.py",
            "score": 0.85,
            "complexity": 3,
            "docstring": "Checks auth token",
        }],
        git_data=[],
        intent_type="semantic",
    )
    assert "auth_check" in ctx