import pytest
from unittest.mock import patch, MagicMock
from app.explainer.prompts import get_prompt
from app.explainer.explainer import get_explanation


# ── prompt tests ───────────────────────────────────────────

def test_get_prompt_structural():
    prompt = get_prompt("structural")
    assert "structural" in prompt.lower() or "calls" in prompt.lower()

def test_get_prompt_semantic():
    prompt = get_prompt("semantic")
    assert "semantic" in prompt.lower() or "relevant" in prompt.lower()

def test_get_prompt_historical():
    prompt = get_prompt("historical")
    assert "historical" in prompt.lower() or "change" in prompt.lower()

def test_get_prompt_unknown_returns_base():
    prompt = get_prompt("unknown_intent")
    assert len(prompt) > 50

def test_all_prompts_contain_rules():
    for intent in ["structural", "semantic", "historical", "hybrid", "full"]:
        prompt = get_prompt(intent)
        assert "function names" in prompt.lower() or "file paths" in prompt.lower()


# ── availability tests ─────────────────────────────────────

def test_is_available_false_without_key():
    import app.explainer.explainer as exp_module
    with patch.object(exp_module.os, "getenv", return_value=None):
        assert exp_module.is_available() is False

def test_is_available_true_with_key():
    import app.explainer.explainer as exp_module
    with patch.object(exp_module.os, "getenv", return_value="sk-test-key"):
        assert exp_module.is_available() is True


# ── explainer tests (mocked API) ──────────────────────────

@pytest.mark.asyncio
async def test_get_explanation_returns_string():
    # mock the OpenAI response structure
    mock_message  = MagicMock()
    mock_message.content = "This is a test explanation about the codebase."

    mock_choice   = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = mock_response

    with patch("app.explainer.explainer.get_client", return_value=mock_instance):
        result = await get_explanation(
            context="USER QUESTION: What does validate call?\n\nFunctions: check, sanitize",
            intent_type="structural",
        )
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_get_explanation_handles_missing_key():
    with patch("app.explainer.explainer.get_client") as mock_client:
        mock_client.side_effect = ValueError("OPENAI_API_KEY not set")
        result = await get_explanation(
            context="test context",
            intent_type="semantic",
        )
        assert "Error" in result


@pytest.mark.asyncio
async def test_get_explanation_handles_auth_error():
    import httpx
    from openai import AuthenticationError as OAIAuthError

    # build a proper httpx request + response pair
    mock_request  = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(401, request=mock_request)

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = OAIAuthError(
        message="Invalid API key",
        response=mock_response,
        body={"error": {"message": "Invalid API key"}},
    )

    with patch("app.explainer.explainer.get_client", return_value=mock_instance):
        result = await get_explanation(
            context="test context",
            intent_type="structural",
        )
        assert "Error" in result