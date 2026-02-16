"""Unit tests for human_review_test_cases_node."""

from unittest.mock import patch

from src.graph.nodes.human_review_test_cases import human_review_test_cases_node
from src.graph.state import (
    TeamContext,
    FrameworkType,
    WorkflowStage,
    JudgeResult,
    JudgeEvaluation,
    create_initial_state,
)


DUMMY_CONTEXT = TeamContext(
    tech_context_md="Python 3.12, pytest",
    codebase_map_md="No existing code",
    framework_type=FrameworkType.API,
    conventions_summary="Use snake_case",
)


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_test_cases_approve(mock_interrupt):
    """APPROVE should route to CODE_STRUCTURE_PLANNING."""
    mock_interrupt.return_value = {
        "decision": "APPROVE",
        "feedback": "Gherkin looks good",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["gherkin_content"] = "Feature: Login\n  Scenario: Valid login"
    state["current_test_cases_version"] = 1
    state["judge_test_cases_evaluation"] = JudgeEvaluation(
        score=90.0,
        result=JudgeResult.PASS,
        feedback="Well structured",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_test_cases_node(state)
    
    assert result["current_stage"] == WorkflowStage.CODE_STRUCTURE_PLANNING
    assert result["approval_gates"]["test_cases"].status == "approved"


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_test_cases_reject(mock_interrupt):
    """REJECT should route to TEST_CASE_GENERATION."""
    mock_interrupt.return_value = {
        "decision": "REJECT",
        "feedback": "Missing negative test cases",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["gherkin_content"] = "Feature: Login\n  Scenario: Valid login"
    state["current_test_cases_version"] = 1
    
    result = human_review_test_cases_node(state)
    
    assert result["current_stage"] == WorkflowStage.TEST_CASE_GENERATION
    assert result["approval_gates"]["test_cases"].status == "rejected"