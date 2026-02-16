# tests/unit/test_code_structure_planning_node.py
"""
Unit tests for Code Structure Planning Node
"""
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.code_structure_planning import code_structure_planning_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, 
    WorkflowStage, DocumentVersion
)
from src.agents.llm_client import LLMResponse

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e testing", 
    codebase_map_md="# Existing Utilities\n- CommonUtils.login()\n- PageBase class",
    framework_type=FrameworkType.UI_E2E, 
    conventions_summary="Use Page Object Model, snake_case for methods"
)

MOCK_CODE_PLAN = """# Code Structure Plan

## 1. File Structure
tests/
  test_login.py [NEW] (~150 LOC)
  pages/
    login_page.py [NEW] (~80 LOC)
  utils/
    common_utils.py [EXISTING - REUSE: tests/utils/common_utils.py]

## 2. Page Objects Design
class LoginPage:
    def __init__(self, page: Page):
        pass
    
    def navigate_to_login(self) -> None:
        pass

## 3. Test File Structure
test_login.py implements TC_LOGIN_001, TC_LOGIN_002

## 4. Utility Reuse Strategy
| Need | Existing Utility | New Utility |
|------|-----------------|-------------|
| Auth | CommonUtils.login() [REUSE] | None |

## 5. Import Strategy
# test_login.py imports:
from pages.login_page import LoginPage
from utils.common_utils import CommonUtils

## 6. Test Data Organization
fixtures/login_data.json

## 7. Naming Conventions
test_<feature>.py, <Feature>Page

## 8. Complexity Estimation
test_login.py: 150 LOC, MEDIUM
login_page.py: 80 LOC, LOW

## 9. Validation Checklist
- [ ] All test cases mapped
- [ ] Existing utilities reused
"""


@patch("src.graph.nodes.code_structure_planning.call_llm")
def test_creates_document_version(mock_llm):
    """Should create DocumentVersion with correct fields."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_CODE_PLAN,
        input_tokens=500,
        output_tokens=1200,
        cost_usd=0.05,
        trace_name="code_structure_planning",
        model_id="test-model",
        latency_ms=2000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    result = code_structure_planning_node(state)
    
    assert result["code_plan_content"] == MOCK_CODE_PLAN
    assert result["current_code_plan_version"] == 1
    assert len(result["code_plan_history"]) == 1
    assert isinstance(result["code_plan_history"][0], DocumentVersion)
    assert result["code_plan_history"][0].document_type == "code_plan"


@patch("src.graph.nodes.code_structure_planning.call_llm")
def test_uses_correct_trace_name_and_params(mock_llm):
    """Should call LLM with trace_name='code_structure_planning' and correct params."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_CODE_PLAN,
        input_tokens=500,
        output_tokens=1200,
        cost_usd=0.05,
        trace_name="code_structure_planning",
        model_id="test-model",
        latency_ms=2000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    result = code_structure_planning_node(state)
    
    # Verify call_llm was called with correct parameters
    mock_llm.assert_called_once()
    call_args = mock_llm.call_args
    assert call_args[1]["trace_name"] == "code_structure_planning"
    assert call_args[1]["temperature"] == 0.2
    assert call_args[1]["max_tokens"] == 16384


@patch("src.graph.nodes.code_structure_planning.call_llm")
def test_reads_codebase_map_from_team_context(mock_llm):
    """Should read codebase_map_md from team_context."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_CODE_PLAN,
        input_tokens=500,
        output_tokens=1200,
        cost_usd=0.05,
        trace_name="code_structure_planning",
        model_id="test-model",
        latency_ms=2000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    result = code_structure_planning_node(state)
    
    # Verify the user prompt includes codebase_map_md
    call_args = mock_llm.call_args
    user_prompt = call_args[1]["user_prompt"]
    assert "CommonUtils.login()" in user_prompt  # From codebase_map_md


@patch("src.graph.nodes.code_structure_planning.call_llm")
def test_routes_to_judge_code_plan(mock_llm):
    """Should route to JUDGE_CODE_PLAN stage."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_CODE_PLAN,
        input_tokens=500,
        output_tokens=1200,
        cost_usd=0.05,
        trace_name="code_structure_planning",
        model_id="test-model",
        latency_ms=2000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    result = code_structure_planning_node(state)
    
    assert result["current_stage"] == WorkflowStage.JUDGE_CODE_PLAN