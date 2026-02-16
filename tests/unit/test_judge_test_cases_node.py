"""Unit tests for judge_test_cases_node."""

import json
from unittest.mock import MagicMock, patch

from src.graph.nodes.judge_test_cases import judge_test_cases_node
from src.graph.state import (
    TeamContext,
    FrameworkType,
    WorkflowStage,
    JudgeResult,
    create_initial_state,
)


DUMMY_CONTEXT = TeamContext(
    tech_context_md="Python 3.12, pytest",
    codebase_map_md="No existing code",
    framework_type=FrameworkType.API,
    conventions_summary="Use snake_case",
)

PASS_RESPONSE = json.dumps({
    "score": 90,
    "result": "PASS",
    "feedback": "Gherkin scenarios are well-structured and traceable.",
    "issues": [],
    "recommendations": [],
    "human_question": None,
})

FAIL_RESPONSE = json.dumps({
    "score": 58,
    "result": "FAIL",
    "feedback": "Missing @TC tags on some scenarios.",
    "issues": [{"type": "traceability", "description": "No tags", "severity": "high"}],
    "recommendations": ["Add @TC tags"],
    "human_question": None,
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_test_cases_pass_routes_to_human_review(mock_llm):
    """PASS should route to HUMAN_REVIEW_TEST_CASES."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["gherkin_content"] = "Feature: Login\n  Scenario: Valid login"
    state["strategy_content"] = "# Strategy\nTC_001: Login test"
    
    result = judge_test_cases_node(state)
    
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_TEST_CASES
    assert result["judge_test_cases_evaluation"].result == JudgeResult.PASS


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_test_cases_fail_routes_to_regenerate(mock_llm):
    """FAIL should route to TEST_CASE_GENERATION."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["gherkin_content"] = "Feature: Login\n  Scenario: Valid login"
    state["strategy_content"] = "# Strategy\nTC_001: Login test"
    
    result = judge_test_cases_node(state)
    
    assert result["current_stage"] == WorkflowStage.TEST_CASE_GENERATION
    assert result["judge_test_cases_evaluation"].result == JudgeResult.FAIL