"""Unit tests for human_review_code_plan_node."""

from unittest.mock import patch

from src.graph.nodes.human_review_code_plan import human_review_code_plan_node
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
def test_human_review_code_plan_approve(mock_interrupt):
    """APPROVE should route to SCRIPTING."""
    mock_interrupt.return_value = {
        "decision": "APPROVE",
        "feedback": "Code plan is solid",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\ntest_login.py [NEW]"
    state["current_code_plan_version"] = 1
    state["judge_code_plan_evaluation"] = JudgeEvaluation(
        score=85.0,
        result=JudgeResult.PASS,
        feedback="Follows conventions",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_code_plan_node(state)
    
    assert result["current_stage"] == WorkflowStage.SCRIPTING
    assert result["approval_gates"]["code_plan"].status == "approved"


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_code_plan_reject(mock_interrupt):
    """REJECT should route to CODE_STRUCTURE_PLANNING."""
    mock_interrupt.return_value = {
        "decision": "REJECT",
        "feedback": "Use existing LoginHelper instead of creating new one",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\ntest_login.py [NEW]"
    state["current_code_plan_version"] = 1
    
    result = human_review_code_plan_node(state)
    
    assert result["current_stage"] == WorkflowStage.CODE_STRUCTURE_PLANNING
    assert result["approval_gates"]["code_plan"].status == "rejected"