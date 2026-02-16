"""Unit tests for human_review_spec_node."""

from unittest.mock import patch

from src.graph.nodes.human_review_spec import human_review_spec_node
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
def test_human_review_spec_approve(mock_interrupt):
    """APPROVE should route to STRATEGY."""
    mock_interrupt.return_value = {
        "decision": "APPROVE",
        "feedback": "Looks good!",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Spec\nFR-001: Login"
    state["current_requirements_spec_version"] = 1
    state["judge_requirements_evaluation"] = JudgeEvaluation(
        score=85.0,
        result=JudgeResult.PASS,
        feedback="Good spec",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_spec_node(state)
    
    # Verify routing
    assert result["current_stage"] == WorkflowStage.STRATEGY
    
    # Verify approval gate updated
    assert "approval_gates" in result
    assert result["approval_gates"]["spec"].status == "approved"
    assert result["approval_gates"]["spec"].reviewer == "human"


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_spec_reject(mock_interrupt):
    """REJECT should route to REQUIREMENTS_SPEC_GEN."""
    mock_interrupt.return_value = {
        "decision": "REJECT",
        "feedback": "Missing edge cases section.",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Spec\nFR-001: Login"
    state["current_requirements_spec_version"] = 1
    state["judge_requirements_evaluation"] = JudgeEvaluation(
        score=85.0,
        result=JudgeResult.PASS,
        feedback="Good spec",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_spec_node(state)
    
    # Verify routing to regenerate
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    
    # Verify approval gate updated
    assert result["approval_gates"]["spec"].status == "rejected"
    
    # Verify feedback stored
    assert "human_feedback" in result
    assert result["human_feedback"] == "Missing edge cases section."


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_spec_edit(mock_interrupt):
    """EDIT should update content and route to STRATEGY."""
    edited_spec = "# Spec (Edited)\nFR-001: Login\nFR-002: Logout"
    
    mock_interrupt.return_value = {
        "decision": "EDIT",
        "feedback": "Added logout requirement",
        "edited_content": edited_spec,
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["requirements_spec_content"] = "# Spec\nFR-001: Login"
    state["current_requirements_spec_version"] = 1
    state["judge_requirements_evaluation"] = JudgeEvaluation(
        score=85.0,
        result=JudgeResult.PASS,
        feedback="Good spec",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_spec_node(state)
    
    # Verify routing
    assert result["current_stage"] == WorkflowStage.STRATEGY
    
    # Verify edited content stored
    assert "requirements_spec_content" in result
    assert result["requirements_spec_content"] == edited_spec
    
    # Verify approval gate updated
    assert result["approval_gates"]["spec"].status == "approved"
    assert "with edits" in result["approval_gates"]["spec"].feedback