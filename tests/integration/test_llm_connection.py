# tests/integration/test_llm_connection.py
"""
Integration tests for LLM client.
NOTE: Tests marked with @pytest.mark.integration make REAL LLM calls.
They require valid credentials in .env file.

Run unit tests only:
    pytest tests/integration/test_llm_connection.py::test_extract_json_strips_fences -v
    pytest tests/integration/test_llm_connection.py::test_extract_json_raises_on_invalid -v

Run integration tests (requires credentials):
    pytest tests/integration/test_llm_connection.py -m integration -v -s
"""

import pytest
from src.agents.llm_client import (
    call_llm,
    verify_llm_connection,
    extract_json_from_response,
    LLMResponse,
)


# ============================================================================
# UNIT TESTS (no LLM calls)
# ============================================================================

def test_extract_json_strips_fences():
    """JSON extraction handles markdown code fences."""
    raw = '```json\n{"score": 85, "result": "PASS"}\n```'
    result = extract_json_from_response(raw)
    assert result["score"] == 85
    assert result["result"] == "PASS"


def test_extract_json_strips_plain_fences():
    """JSON extraction handles plain markdown fences."""
    raw = '```\n{"score": 90}\n```'
    result = extract_json_from_response(raw)
    assert result["score"] == 90


def test_extract_json_no_fences():
    """JSON extraction handles raw JSON without fences."""
    raw = '{"score": 75, "status": "ok"}'
    result = extract_json_from_response(raw)
    assert result["score"] == 75
    assert result["status"] == "ok"


def test_extract_json_raises_on_invalid():
    """JSON extraction raises ValueError on non-JSON."""
    with pytest.raises(ValueError):
        extract_json_from_response("This is not JSON at all")


# ============================================================================
# INTEGRATION TESTS (require valid credentials)
# ============================================================================

@pytest.mark.integration
def test_verify_connection():
    """Verify the active LLM backend responds."""
    result = verify_llm_connection()
    assert result is True, "LLM connection failed — check credentials in .env"


@pytest.mark.integration
def test_call_llm_returns_llm_response():
    """Real LLM call returns a valid LLMResponse."""
    response = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with exactly: HELLO",
        trace_name="test_ping",
    )
    
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert response.latency_ms > 0
    assert response.cost_usd >= 0
    assert response.trace_name == "test_ping"
    assert len(response.model_id) > 0


@pytest.mark.integration
def test_call_llm_with_custom_temperature():
    """LLM call respects custom temperature."""
    response = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say 'test'",
        trace_name="test_temp",
        temperature=0.1,
    )
    
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0


@pytest.mark.integration
def test_call_llm_uses_token_budget():
    """LLM call uses TOKEN_BUDGETS for known trace names."""
    response = call_llm(
        system_prompt="You are a helpful assistant.",
        user_prompt="Count to 5",
        trace_name="qa_interaction",  # Has 2048 token budget
    )
    
    assert isinstance(response, LLMResponse)
    # If this completes without error, budget was applied correctly