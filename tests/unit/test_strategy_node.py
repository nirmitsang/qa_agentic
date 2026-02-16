# tests/unit/test_strategy_node.py
"""
Unit tests for Strategy Generation Node
"""
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.strategy import strategy_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, 
    WorkflowStage, DocumentVersion
)
from src.agents.llm_client import LLMResponse

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", 
    codebase_map_md="# Codebase",
    framework_type=FrameworkType.UI_E2E, 
    conventions_summary="use POM"
)

MOCK_STRATEGY_CONTENT = """# Test Strategy

## 1. Strategy Overview
Comprehensive testing of login functionality.

## 2. Test Scope
In-scope: Login form, authentication, session management
Out-of-scope: Password reset

## 3. Test Types & Rationale
- Functional: Core login flow
- Negative: Invalid credentials
- Security: SQL injection, XSS

## 4. Test Case Summary Table
| ID | Title | Type | Priority | Requirement | Risk |
|----|-------|------|----------|-------------|------|
| TC_LOGIN_001 | Valid login | functional | P0 | FR-001 | HIGH |
| TC_LOGIN_002 | Invalid credentials | negative | P1 | FR-002 | MEDIUM |

## 5. Priority Justification
P0: Critical user path

## 6. Coverage Matrix
FR-001 → TC_LOGIN_001
FR-002 → TC_LOGIN_002

## 7. Test Environment Requirements
- Staging environment with test users

## 8. Estimated Effort
Total: 8 hours
"""


@patch("src.graph.nodes.strategy.call_llm")
def test_creates_document_version(mock_llm):
    """Should create DocumentVersion with correct fields."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_STRATEGY_CONTENT,
        input_tokens=300,
        output_tokens=800,
        cost_usd=0.03,
        trace_name="strategy",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Requirements..."
    result = strategy_node(state)
    
    assert result["strategy_content"] == MOCK_STRATEGY_CONTENT
    assert result["current_strategy_version"] == 1
    assert len(result["strategy_history"]) == 1
    assert isinstance(result["strategy_history"][0], DocumentVersion)
    assert result["strategy_history"][0].document_type == "strategy"
    assert result["strategy_history"][0].version == 1


@patch("src.graph.nodes.strategy.call_llm")
def test_increments_version_on_retry(mock_llm):
    """Should increment version number on retry."""
    mock_llm.return_value = LLMResponse(
        content="# Strategy v2\n...",
        input_tokens=300,
        output_tokens=800,
        cost_usd=0.03,
        trace_name="strategy",
        model_id="test-model",
        latency_ms=1500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Requirements..."
    state["current_strategy_version"] = 1
    state["strategy_iteration_count"] = 1
    result = strategy_node(state)
    
    assert result["current_strategy_version"] == 2
    assert result["strategy_iteration_count"] == 2


@patch("src.graph.nodes.strategy.call_llm")
def test_routes_to_judge_strategy(mock_llm):
    """Should route to JUDGE_STRATEGY stage."""
    mock_llm.return_value = LLMResponse(
        content="# Strategy",
        input_tokens=200,
        output_tokens=400,
        cost_usd=0.02,
        trace_name="strategy",
        model_id="test-model",
        latency_ms=1000,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["requirements_spec_content"] = "# Requirements..."
    result = strategy_node(state)
    
    assert result["current_stage"] == WorkflowStage.JUDGE_STRATEGY