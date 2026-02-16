# tests/unit/test_requirements_spec_gen_node.py
"""
Unit tests for Requirements Spec Generation Node
"""
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.requirements_spec_gen import requirements_spec_gen_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType, 
    WorkflowStage, DocumentVersion
)
from src.agents.llm_client import LLMResponse

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", 
    codebase_map_md="# Codebase",
    framework_type=FrameworkType.API, 
    conventions_summary="use httpx"
)

MOCK_SPEC_CONTENT = """# Requirements Specification

## 1. Overview
Test the login API endpoint.

## 2. Functional Requirements
FR-001: System MUST accept valid credentials
FR-002: System MUST reject invalid credentials

## 3. Non-Functional Requirements
NFR-001: Response time MUST be < 200ms

## 4. Acceptance Criteria
FR-001: Given valid credentials, When POST /login, Then return 200 OK

## 5. Edge Cases & Boundary Conditions
- Empty username
- SQL injection attempts

## 6. Out of Scope
Password reset functionality

## 7. Test Data Requirements
Valid: user@example.com / password123

## 8. Dependencies & Assumptions
Assumes database is seeded

## 9. Risk Assessment
Risk Level: MEDIUM
"""


@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_creates_document_version(mock_llm):
    """Should create DocumentVersion with correct fields."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_SPEC_CONTENT,
        input_tokens=200,
        output_tokens=500,
        cost_usd=0.02,
        trace_name="requirements_spec_gen",
        model_id="test-model",
        latency_ms=1000,
    )
    state = create_initial_state("Test API login", DUMMY_CONTEXT, "team", 0.85)
    result = requirements_spec_gen_node(state)
    
    assert result["requirements_spec_content"] == MOCK_SPEC_CONTENT
    assert result["current_requirements_spec_version"] == 1
    assert len(result["requirements_spec_history"]) == 1
    assert isinstance(result["requirements_spec_history"][0], DocumentVersion)
    assert result["requirements_spec_history"][0].document_type == "requirements_spec"
    assert result["requirements_spec_history"][0].version == 1


@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_increments_version_on_retry(mock_llm):
    """Should increment version number on retry."""
    mock_llm.return_value = LLMResponse(
        content="# Requirements v2\n...",
        input_tokens=200,
        output_tokens=500,
        cost_usd=0.02,
        trace_name="requirements_spec_gen",
        model_id="test-model",
        latency_ms=1000,
    )
    state = create_initial_state("Test API login", DUMMY_CONTEXT, "team", 0.85)
    state["current_requirements_spec_version"] = 1
    state["requirements_iteration_count"] = 1
    result = requirements_spec_gen_node(state)
    
    assert result["current_requirements_spec_version"] == 2
    assert result["requirements_iteration_count"] == 2


@patch("src.graph.nodes.requirements_spec_gen.call_llm")
def test_routes_to_judge_requirements(mock_llm):
    """Should route to JUDGE_REQUIREMENTS stage."""
    mock_llm.return_value = LLMResponse(
        content="# Spec",
        input_tokens=100,
        output_tokens=200,
        cost_usd=0.01,
        trace_name="requirements_spec_gen",
        model_id="test-model",
        latency_ms=500,
    )
    state = create_initial_state("Test API login", DUMMY_CONTEXT, "team", 0.85)
    result = requirements_spec_gen_node(state)
    
    assert result["current_stage"] == WorkflowStage.JUDGE_REQUIREMENTS