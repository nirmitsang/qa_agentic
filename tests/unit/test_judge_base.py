"""
Unit tests for the shared judge base function.

Tests cover:
- PASS routing
- FAIL routing
- NEEDS_HUMAN routing
- Final iteration override (FAIL → NEEDS_HUMAN)
- Error handling
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.graph.nodes._judge_base import run_judge
from src.graph.state import (
    AgentState,
    TeamContext,
    FrameworkType,
    WorkflowStage,
    WorkflowStatus,
    JudgeResult,
    create_initial_state,
)


# Test fixtures
DUMMY_CONTEXT = TeamContext(
    tech_context_md="Python 3.12, pytest",
    codebase_map_md="No existing code",
    framework_type=FrameworkType.API,
    conventions_summary="Use snake_case",
)

PASS_RESPONSE = json.dumps({
    "score": 85,
    "result": "PASS",
    "feedback": "Document meets quality standards. All sections complete.",
    "issues": [],
    "recommendations": ["Consider adding more edge cases"],
    "human_question": None,
})

FAIL_RESPONSE = json.dumps({
    "score": 55,
    "result": "FAIL",
    "feedback": "Document is incomplete. Missing critical sections.",
    "issues": [
        {"type": "completeness", "description": "Missing edge cases section", "severity": "high"}
    ],
    "recommendations": ["Add edge cases", "Clarify acceptance criteria"],
    "human_question": None,
})

NEEDS_HUMAN_RESPONSE = json.dumps({
    "score": 72,
    "result": "NEEDS_HUMAN",
    "feedback": "Ambiguous requirements detected. Human clarification needed.",
    "issues": [
        {"type": "ambiguity", "description": "FR-003 is vague", "severity": "medium"}
    ],
    "recommendations": [],
    "human_question": "Should FR-003 include offline mode or online-only?",
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_pass_routes_correctly(mock_llm):
    """PASS result should route to pass_stage."""
    mock_llm.return_value = MagicMock(
        content=PASS_RESPONSE,
        cost_usd=0.01,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify routing
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    
    # Verify evaluation stored
    assert "judge_requirements_evaluation" in result
    evaluation = result["judge_requirements_evaluation"]
    assert evaluation.score == 85
    assert evaluation.result == JudgeResult.PASS
    assert "quality standards" in evaluation.feedback
    assert len(evaluation.recommendations) == 1
    
    # Verify cost tracking
    assert "accumulated_cost_usd" in result
    assert result["accumulated_cost_usd"] == 0.01


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_fail_routes_to_regenerate(mock_llm):
    """FAIL result should route to failure_stage (regenerate)."""
    mock_llm.return_value = MagicMock(
        content=FAIL_RESPONSE,
        cost_usd=0.01,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify routing to regenerate
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    
    # Verify evaluation
    evaluation = result["judge_requirements_evaluation"]
    assert evaluation.score == 55
    assert evaluation.result == JudgeResult.FAIL
    assert "incomplete" in evaluation.feedback.lower()
    assert len(evaluation.issues) == 1
    assert evaluation.issues[0]["type"] == "completeness"


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_needs_human_routes_to_human_review(mock_llm):
    """NEEDS_HUMAN result should route to human_review_stage."""
    mock_llm.return_value = MagicMock(
        content=NEEDS_HUMAN_RESPONSE,
        cost_usd=0.01,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify routing to human review
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    
    # Verify evaluation
    evaluation = result["judge_requirements_evaluation"]
    assert evaluation.score == 72
    assert evaluation.result == JudgeResult.NEEDS_HUMAN
    assert "ambiguous" in evaluation.feedback.lower()


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_fail_at_max_iterations_escalates_to_human(mock_llm):
    """
    CRITICAL TEST: On final iteration, FAIL should become NEEDS_HUMAN.
    This prevents infinite regeneration loops.
    """
    mock_llm.return_value = MagicMock(
        content=FAIL_RESPONSE,
        cost_usd=0.01,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    # Set iteration count to 2 (final iteration, since max=3)
    state["requirements_iteration_count"] = 2
    state["max_judge_iterations"] = 3
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # MUST route to human review, not regenerate
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    
    # Verify evaluation was overridden
    evaluation = result["judge_requirements_evaluation"]
    assert evaluation.result == JudgeResult.NEEDS_HUMAN  # Overridden from FAIL
    assert "MAX ITERATIONS REACHED" in evaluation.feedback
    assert "regenerated 2 times" in evaluation.feedback


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_handles_llm_failure(mock_llm):
    """LLM failures should return FAILED status."""
    mock_llm.side_effect = RuntimeError("Connection timeout")
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify failure state
    assert result["workflow_status"] == WorkflowStatus.FAILED
    assert result["current_stage"] == WorkflowStage.FAILED
    assert "Connection timeout" in result["error_message"]


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_handles_invalid_json(mock_llm):
    """Invalid JSON responses should return FAILED status."""
    mock_llm.return_value = MagicMock(
        content=json.dumps({"score": 85}),  # Missing required fields
        cost_usd=0.01,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify failure state
    assert result["workflow_status"] == WorkflowStatus.FAILED
    assert result["current_stage"] == WorkflowStage.FAILED
    # Fixed: check for lowercase "invalid json" since we call .lower()
    assert "invalid json" in result["error_message"].lower()


@patch("src.graph.nodes._judge_base.call_llm")
def test_run_judge_accumulates_cost_correctly(mock_llm):
    """Cost should accumulate across multiple judge calls."""
    mock_llm.return_value = MagicMock(
        content=PASS_RESPONSE,
        cost_usd=0.02,
        input_tokens=100,
        output_tokens=50,
    )
    
    state = create_initial_state(
        raw_input="Test input",
        team_context=DUMMY_CONTEXT,
        team_id="team_1",
        qa_confidence_threshold=0.85,
    )
    # Simulate existing accumulated cost
    state["accumulated_cost_usd"] = 0.15
    
    result = run_judge(
        state=state,
        system_prompt="You are a requirements judge",
        user_prompt="Evaluate this document",
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )
    
    # Verify cost accumulation
    # Fixed: use pytest.approx() for floating point comparison
    assert result["accumulated_cost_usd"] == pytest.approx(0.17)