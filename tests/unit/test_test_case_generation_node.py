# tests/unit/test_test_case_generation_node.py
"""
Unit tests for Test Case Generation Node
"""
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.test_case_generation import test_case_generation_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, 
    WorkflowStage
)
from src.agents.llm_client import LLMResponse

VALID_GHERKIN = """Feature: Login
  
  @TC_LOGIN_001 @functional @P0
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
"""

INVALID_GHERKIN = "This is not valid Gherkin syntax at all"

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", 
    codebase_map_md="",
    framework_type=FrameworkType.UI_E2E, 
    conventions_summary=""
)


@patch("src.graph.nodes.test_case_generation.call_llm")
def test_valid_gherkin_passes_through(mock_llm):
    """Valid Gherkin should pass validation on first attempt."""
    mock_llm.return_value = LLMResponse(
        content=VALID_GHERKIN,
        input_tokens=400,
        output_tokens=200,
        cost_usd=0.02,
        trace_name="test_case_generation",
        model_id="test-model",
        latency_ms=1000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["strategy_content"] = "# Strategy..."
    state["requirements_spec_content"] = "# Requirements..."
    result = test_case_generation_node(state)
    
    assert result["gherkin_validation_passed"] is True
    assert result["gherkin_content"] == VALID_GHERKIN
    assert mock_llm.call_count == 1  # No retry needed


@patch("src.graph.nodes.test_case_generation.call_llm")
def test_invalid_gherkin_triggers_internal_retry(mock_llm):
    """Invalid Gherkin should trigger internal retry with error feedback."""
    mock_llm.side_effect = [
        LLMResponse(
            content=INVALID_GHERKIN,
            input_tokens=400,
            output_tokens=100,
            cost_usd=0.01,
            trace_name="test_case_generation",
            model_id="test-model",
            latency_ms=800,
        ),
        LLMResponse(
            content=VALID_GHERKIN,
            input_tokens=450,
            output_tokens=200,
            cost_usd=0.02,
            trace_name="test_case_generation",
            model_id="test-model",
            latency_ms=1000,
        ),
    ]
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["strategy_content"] = "# Strategy..."
    state["requirements_spec_content"] = "# Requirements..."
    result = test_case_generation_node(state)
    
    assert mock_llm.call_count == 2  # Retry happened
    assert result["gherkin_validation_passed"] is True
    assert result["gherkin_content"] == VALID_GHERKIN


@patch("src.graph.nodes.test_case_generation.call_llm")
def test_routes_to_judge_test_cases(mock_llm):
    """Should route to JUDGE_TEST_CASES stage."""
    mock_llm.return_value = LLMResponse(
        content=VALID_GHERKIN,
        input_tokens=400,
        output_tokens=200,
        cost_usd=0.02,
        trace_name="test_case_generation",
        model_id="test-model",
        latency_ms=1000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["strategy_content"] = "# Strategy..."
    state["requirements_spec_content"] = "# Requirements..."
    result = test_case_generation_node(state)
    
    assert result["current_stage"] == WorkflowStage.JUDGE_TEST_CASES