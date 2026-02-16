"""Unit tests for judge_requirements_node."""

import json
from unittest.mock import MagicMock, patch

from src.graph.nodes.judge_requirements import judge_requirements_node
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
    "score": 85,
    "result": "PASS",
    "feedback": "Requirements are complete and testable.",
    "issues": [],
    "recommendations": [],
    "human_question": None,
})

FAIL_RESPONSE = json.dumps({
    "score": 55,
    "result": "FAIL",
    "feedback": "Missing edge cases section.",
    "issues": [{"type": "completeness", "description": "No edge cases", "severity": "high"}],
    "recommendations": ["Add edge cases"],
    "human_question": None,
})

NEEDS_HUMAN_RESPONSE = json.dumps({
    "score": 72,
    "result": "NEEDS_HUMAN",
    "feedback": "Ambiguous requirement FR-003.",
    "issues": [],
    "recommendations": [],
    "human_question": "Should FR-003 include offline mode?",
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_requirements_pass_routes_to_human_review(mock_llm):
    """PASS should route to HUMAN_REVIEW_SPEC."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Requirements Spec\n\nFR-001: User can login"
    
    result = judge_requirements_node(state)
    
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert result["judge_requirements_evaluation"].result == JudgeResult.PASS
    assert result["judge_requirements_evaluation"].score == 85


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_requirements_fail_routes_to_regenerate(mock_llm):
    """FAIL should route to REQUIREMENTS_SPEC_GEN."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Requirements Spec\n\nFR-001: User can login"
    
    result = judge_requirements_node(state)
    
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    assert result["judge_requirements_evaluation"].result == JudgeResult.FAIL
    assert result["judge_requirements_evaluation"].score == 55


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_requirements_needs_human_routes_to_human_review(mock_llm):
    """NEEDS_HUMAN should route to HUMAN_REVIEW_SPEC."""
    mock_llm.return_value = MagicMock(content=NEEDS_HUMAN_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Requirements Spec\n\nFR-001: User can login"
    
    result = judge_requirements_node(state)
    
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert result["judge_requirements_evaluation"].result == JudgeResult.NEEDS_HUMAN


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_requirements_final_iteration_override(mock_llm):
    """Final iteration FAIL should escalate to NEEDS_HUMAN."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Requirements Spec\n\nFR-001: User can login"
    state["requirements_iteration_count"] = 2  # Final iteration (max=3)
    
    result = judge_requirements_node(state)
    
    # Should route to human review, not regenerate
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_SPEC
    assert result["judge_requirements_evaluation"].result == JudgeResult.NEEDS_HUMAN