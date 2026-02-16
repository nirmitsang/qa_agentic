"""Unit tests for judge_code_node."""

import json
from unittest.mock import MagicMock, patch

from src.graph.nodes.judge_code import judge_code_node
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
    "score": 92,
    "result": "PASS",
    "feedback": "Script follows plan, has good coverage, clean code.",
    "issues": [],
    "recommendations": [],
    "human_question": None,
})

FAIL_RESPONSE = json.dumps({
    "score": 55,
    "result": "FAIL",
    "feedback": "Script deviates from approved plan.",
    "issues": [
        {"type": "plan_adherence", "description": "Created new utility instead of using existing", "severity": "high"}
    ],
    "recommendations": ["Follow the approved code plan"],
    "human_question": None,
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_pass_routes_to_human_review(mock_llm):
    """PASS should route to HUMAN_REVIEW_CODE."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["script_content"] = "import pytest\ndef test_login(): assert True"
    state["code_plan_content"] = "# Plan\ntest_login.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_node(state)
    
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_CODE
    assert result["judge_code_evaluation"].result == JudgeResult.PASS


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_fail_routes_to_regenerate(mock_llm):
    """FAIL should route to SCRIPTING."""
    mock_llm.return_value = MagicMock(content=FAIL_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["script_content"] = "import pytest\ndef test_login(): assert True"
    state["code_plan_content"] = "# Plan\ntest_login.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_node(state)
    
    assert result["current_stage"] == WorkflowStage.SCRIPTING
    assert result["judge_code_evaluation"].result == JudgeResult.FAIL