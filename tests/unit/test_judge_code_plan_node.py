"""Unit tests for judge_code_plan_node with special routing."""

import json
from unittest.mock import MagicMock, patch

from src.graph.nodes.judge_code_plan import judge_code_plan_node
from src.graph.state import (
    TeamContext,
    FrameworkType,
    WorkflowStage,
    JudgeResult,
    create_initial_state,
)


DUMMY_CONTEXT = TeamContext(
    tech_context_md="Python 3.12, pytest",
    codebase_map_md="# Existing Utilities\nclass LoginHelper: ...",
    framework_type=FrameworkType.API,
    conventions_summary="Use snake_case",
)

PASS_RESPONSE = json.dumps({
    "score": 85,
    "result": "PASS",
    "feedback": "Code plan follows conventions and reuses utilities correctly.",
    "issues": [],
    "recommendations": [],
    "human_question": None,
})

FAIL_MINOR_RESPONSE = json.dumps({
    "score": 65,
    "result": "FAIL",
    "feedback": "File organization could be improved.",
    "issues": [
        {"type": "organization", "description": "Consider splitting large file", "severity": "low"}
    ],
    "recommendations": ["Split test_login.py into smaller files"],
    "human_question": None,
})

FAIL_CRITICAL_DUPLICATE_RESPONSE = json.dumps({
    "score": 45,
    "result": "FAIL",
    "feedback": "Creating duplicate utilities that already exist.",
    "issues": [
        {
            "type": "duplication",
            "description": "Creating duplicate LoginHelper when one exists in codebase_map",
            "severity": "critical",
        }
    ],
    "recommendations": ["Use existing LoginHelper from utils/"],
    "human_question": None,
})

FAIL_CRITICAL_CONVENTION_RESPONSE = json.dumps({
    "score": 50,
    "result": "FAIL",
    "feedback": "Violates team conventions.",
    "issues": [
        {
            "type": "convention",
            "description": "File naming violates convention: using camelCase instead of snake_case",
            "severity": "high",
        }
    ],
    "recommendations": ["Use snake_case naming"],
    "human_question": None,
})


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_plan_pass_routes_to_human_review(mock_llm):
    """PASS should always route to HUMAN_REVIEW_CODE_PLAN."""
    mock_llm.return_value = MagicMock(content=PASS_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\n## File Structure\ntest_login.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_plan_node(state)
    
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_CODE_PLAN
    assert result["judge_code_plan_evaluation"].result == JudgeResult.PASS


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_plan_fail_minor_routes_to_human_review(mock_llm):
    """FAIL with minor issues should route to HUMAN_REVIEW_CODE_PLAN (special routing)."""
    mock_llm.return_value = MagicMock(content=FAIL_MINOR_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\n## File Structure\ntest_login.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_plan_node(state)
    
    # Should route to human review, not regeneration
    assert result["current_stage"] == WorkflowStage.HUMAN_REVIEW_CODE_PLAN
    assert result["judge_code_plan_evaluation"].result == JudgeResult.FAIL


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_plan_fail_critical_duplicate_routes_to_regenerate(mock_llm):
    """FAIL with duplicate utilities should route to CODE_STRUCTURE_PLANNING."""
    mock_llm.return_value = MagicMock(content=FAIL_CRITICAL_DUPLICATE_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\n## File Structure\ntest_login.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_plan_node(state)
    
    # Should route to regeneration due to critical issue
    assert result["current_stage"] == WorkflowStage.CODE_STRUCTURE_PLANNING
    assert result["judge_code_plan_evaluation"].result == JudgeResult.FAIL
    assert any("duplicate" in issue.get("description", "").lower() 
               for issue in result["judge_code_plan_evaluation"].issues)


@patch("src.graph.nodes._judge_base.call_llm")
def test_judge_code_plan_fail_critical_convention_routes_to_regenerate(mock_llm):
    """FAIL with convention violation should route to CODE_STRUCTURE_PLANNING."""
    mock_llm.return_value = MagicMock(content=FAIL_CRITICAL_CONVENTION_RESPONSE, cost_usd=0.01)
    
    state = create_initial_state("Test input", DUMMY_CONTEXT, "team_1", 0.85)
    state["code_plan_content"] = "# Code Plan\n## File Structure\ntestLogin.py [NEW]"
    state["gherkin_content"] = "Feature: Login"
    
    result = judge_code_plan_node(state)
    
    # Should route to regeneration due to critical convention violation
    assert result["current_stage"] == WorkflowStage.CODE_STRUCTURE_PLANNING
    assert result["judge_code_plan_evaluation"].result == JudgeResult.FAIL