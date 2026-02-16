"""Unit tests for human_review_code_node."""

from unittest.mock import patch

from src.graph.nodes.human_review_code import human_review_code_node
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
def test_human_review_code_approve(mock_interrupt):
    """APPROVE should route to COMPLETED (workflow ends)."""
    mock_interrupt.return_value = {
        "decision": "APPROVE",
        "feedback": "Script is ready for use",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["script_content"] = "import pytest\ndef test_login(): assert True"
    state["current_script_version"] = 1
    state["judge_code_evaluation"] = JudgeEvaluation(
        score=92.0,
        result=JudgeResult.PASS,
        feedback="Clean code",
        issues=[],
        recommendations=[],
    )
    
    result = human_review_code_node(state)
    
    assert result["current_stage"] == WorkflowStage.COMPLETED
    assert result["approval_gates"]["code"].status == "approved"


@patch("src.graph.nodes.human_review_spec.interrupt")
def test_human_review_code_reject(mock_interrupt):
    """REJECT should route to SCRIPTING."""
    mock_interrupt.return_value = {
        "decision": "REJECT",
        "feedback": "Add error handling for edge case",
        "edited_content": "",
    }
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["script_content"] = "import pytest\ndef test_login(): assert True"
    state["current_script_version"] = 1
    
    result = human_review_code_node(state)
    
    assert result["current_stage"] == WorkflowStage.SCRIPTING
    assert result["approval_gates"]["code"].status == "rejected"