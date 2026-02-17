"""
Tests for judge_requirements_node (Task 7.2).

Verifies:
- PASS routes to HUMAN_REVIEW_SPEC
- FAIL routes to REQUIREMENTS_SPEC_GEN
- JudgeEvaluation stored in state["judge_requirements_evaluation"]
"""

import json
from unittest.mock import patch, MagicMock

from src.graph.nodes.judge_requirements import judge_requirements_node
from src.graph.state import (
    create_initial_state,
    TeamContext,
    FrameworkType,
    WorkflowStage,
    JudgeResult,
)

DUMMY_CONTEXT = TeamContext("tech", "code", FrameworkType.API, "")

PASS_RESPONSE = json.dumps({
    "score": 85,
    "result": "PASS",
    "feedback": "Good requirements spec.",
    "issues": [],
    "recommendations": [],
    "human_question": None,
})

FAIL_RESPONSE = json.dumps({
    "score": 45,
    "result": "FAIL",
    "feedback": "Missing edge cases and acceptance criteria.",
    "issues": [{"type": "missing", "description": "No error handling cases"}],
    "recommendations": ["Add negative test scenarios"],
    "human_question": None,
})

NEEDS_HUMAN_RESPONSE = json.dumps({
    "score": 65,
    "result": "NEEDS_HUMAN",
    "feedback": "Ambiguous requirements need human clarification.",
    "issues": [],
    "recommendations": [],
    "human_question": "Are these requirements for API or UI testing?",
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_pass_routes_to_human_review_spec(mock_llm):
    """PASS should route to HUMAN_REVIEW_SPEC."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    state = create_initial_state("Test feature", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Requirements Spec"

    result = judge_requirements_node(state)

    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert "judge_requirements_evaluation" in result
    assert result["judge_requirements_evaluation"].result == JudgeResult.PASS
    assert result["judge_requirements_evaluation"].score == 85


@patch("src.graph.nodes._judge_base.call_llm")
def test_fail_routes_to_requirements_spec_gen(mock_llm):
    """FAIL should route back to REQUIREMENTS_SPEC_GEN for regeneration."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    state = create_initial_state("Test feature", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Bad Spec"

    result = judge_requirements_node(state)

    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    assert result["judge_requirements_evaluation"].result == JudgeResult.FAIL
    assert result["judge_requirements_evaluation"].score == 45


@patch("src.graph.nodes._judge_base.call_llm")
def test_needs_human_routes_to_human_review_spec(mock_llm):
    """NEEDS_HUMAN should route to HUMAN_REVIEW_SPEC."""
    mock_llm.return_value = MagicMock(content=NEEDS_HUMAN_RESPONSE, cost_usd=0.01)
    state = create_initial_state("Test feature", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Ambiguous Spec"

    result = judge_requirements_node(state)

    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert result["judge_requirements_evaluation"].result == JudgeResult.NEEDS_HUMAN


@patch("src.graph.nodes._judge_base.call_llm")
def test_evaluation_stored_in_correct_key(mock_llm):
    """JudgeEvaluation must be stored in state['judge_requirements_evaluation']."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    state = create_initial_state("Test feature", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Spec"

    result = judge_requirements_node(state)

    evaluation = result["judge_requirements_evaluation"]
    assert evaluation.feedback == "Good requirements spec."
    assert isinstance(evaluation.issues, list)
    assert isinstance(evaluation.recommendations, list)


@patch("src.graph.nodes._judge_base.call_llm")
def test_fail_at_max_iterations_escalates_to_human(mock_llm):
    """FAIL on final iteration should be overridden to NEEDS_HUMAN."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    state = create_initial_state("Test feature", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Bad Spec"
    state["requirements_iteration_count"] = 2  # At max (3 iterations = index 2)

    result = judge_requirements_node(state)

    # Should escalate to human review instead of looping
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert result["judge_requirements_evaluation"].result == JudgeResult.NEEDS_HUMAN
