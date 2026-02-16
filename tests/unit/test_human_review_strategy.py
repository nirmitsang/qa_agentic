"""Unit tests for human_review_strategy_node."""

from unittest.mock import patch

from src.graph.nodes.human_review_strategy import human_review_strategy_node
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
def test_human_review_strategy_approve(mock_interrupt):
    """APPROVE should route to TEST_CASE_GENERATION."""
    mock_interrupt.return_value = {
        "decision": "APPROVE",
        "feedback": "Strategy looks comprehensive",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["strategy_content"] = "# Strategy\nTC_001: Login test"
    state["current_strategy_version"] = 1
    state["judge_strategy_evaluation"] = JudgeEvaluation(
        score=88.0,
        result=JudgeResult.PASS,
        feedback="Good coverage",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_strategy_node(state)
    
    assert result["current_stage"] == WorkflowStage.TEST_CASE_GENERATION
    assert result["approval_gates"]["strategy"].status == "approved"


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_strategy_reject(mock_interrupt):
    """REJECT should route to STRATEGY."""
    mock_interrupt.return_value = {
        "decision": "REJECT",
        "feedback": "Missing security tests",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["strategy_content"] = "# Strategy\nTC_001: Login test"
    state["current_strategy_version"] = 1
    
    result = human_review_strategy_node(state)
    
    assert result["current_stage"] == WorkflowStage.STRATEGY
    assert result["approval_gates"]["strategy"].status == "rejected"