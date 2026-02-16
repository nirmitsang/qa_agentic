# tests/unit/test_scripting_node.py
"""
Unit tests for Scripting Node
"""
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.scripting import scripting_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, 
    WorkflowStage, DocumentVersion
)
from src.agents.llm_client import LLMResponse

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", 
    codebase_map_md="# Utilities\n- CommonUtils.login()",
    framework_type=FrameworkType.UI_E2E, 
    conventions_summary="POM pattern"
)

MOCK_SCRIPT_CONTENT = '''"""Test login functionality"""
import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
from utils.common_utils import CommonUtils


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Create LoginPage instance."""
    return LoginPage(page)


def test_valid_login(login_page: LoginPage):
    """Test successful login with valid credentials."""
    login_page.navigate_to_login()
    login_page.enter_credentials("user@example.com", "password123")
    login_page.click_login_button()
    assert login_page.is_dashboard_visible()
'''

MOCK_CODE_PLAN = """# Code Structure Plan
## File Structure
test_login.py [NEW]
pages/login_page.py [NEW]
## Utility Reuse
Use CommonUtils.login()
"""


@patch("src.graph.nodes.scripting.call_llm")
def test_creates_document_version(mock_llm):
    """Should create DocumentVersion with correct fields."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_SCRIPT_CONTENT,
        input_tokens=600,
        output_tokens=400,
        cost_usd=0.03,
        trace_name="scripting",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    state["code_plan_content"] = MOCK_CODE_PLAN
    result = scripting_node(state)
    
    assert result["script_content"] == MOCK_SCRIPT_CONTENT
    assert result["current_script_version"] == 1
    assert len(result["script_history"]) == 1
    assert isinstance(result["script_history"][0], DocumentVersion)
    assert result["script_history"][0].document_type == "script"
    assert result["script_history"][0].format == "python"


@patch("src.graph.nodes.scripting.call_llm")
def test_code_plan_content_is_in_prompt(mock_llm):
    """Should include code_plan_content in the user prompt (PRIMARY input)."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_SCRIPT_CONTENT,
        input_tokens=600,
        output_tokens=400,
        cost_usd=0.03,
        trace_name="scripting",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    state["code_plan_content"] = MOCK_CODE_PLAN
    result = scripting_node(state)
    
    # Verify code_plan_content was included in the prompt
    call_args = mock_llm.call_args
    user_prompt = call_args[1]["user_prompt"]
    assert "Code Structure Plan" in user_prompt
    assert "CommonUtils.login()" in user_prompt


@patch("src.graph.nodes.scripting.call_llm")
def test_routes_to_judge_code(mock_llm):
    """Should route to JUDGE_CODE stage."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_SCRIPT_CONTENT,
        input_tokens=600,
        output_tokens=400,
        cost_usd=0.03,
        trace_name="scripting",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    state["code_plan_content"] = MOCK_CODE_PLAN
    result = scripting_node(state)
    
    assert result["current_stage"] == WorkflowStage.JUDGE_CODE


@patch("src.graph.nodes.scripting.call_llm")
def test_sets_script_filename(mock_llm):
    """Should set script_filename field."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_SCRIPT_CONTENT,
        input_tokens=600,
        output_tokens=400,
        cost_usd=0.03,
        trace_name="scripting",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["gherkin_content"] = "Feature: Login..."
    state["code_plan_content"] = MOCK_CODE_PLAN
    result = scripting_node(state)
    
    assert result["script_filename"] == "test_generated.py"