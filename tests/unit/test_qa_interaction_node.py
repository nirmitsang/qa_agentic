# tests/unit/test_qa_interaction_node.py
"""
Unit tests for QA Interaction Node
"""
import json
from unittest.mock import patch, MagicMock
import pytest
from src.graph.nodes.qa_interaction import qa_interaction_node
from src.graph.state import (
    create_initial_state, TeamContext, FrameworkType,
    WorkflowStage, WorkflowStatus, QASession
)
from src.agents.llm_client import LLMResponse

DUMMY_CONTEXT = TeamContext(
    tech_context_md="playwright e2e", 
    codebase_map_md="",
    framework_type=FrameworkType.UI_E2E, 
    conventions_summary=""
)

MOCK_HIGH_CONFIDENCE = json.dumps({
    "ai_confidence": 0.92, 
    "can_proceed": True,
    "framework_type": "UI_E2E", 
    "questions": []
})

MOCK_LOW_CONFIDENCE = json.dumps({
    "ai_confidence": 0.60, 
    "can_proceed": False,
    "framework_type": "UI_E2E",
    "questions": [
        {
            "id": "Q1", 
            "text": "What auth method?", 
            "category": "auth", 
            "is_required": True
        }
    ]
})


@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_proceeds_on_high_confidence(mock_llm):
    """High confidence should proceed to requirements generation."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_HIGH_CONFIDENCE,
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
        trace_name="qa_interaction",
        model_id="test-model",
        latency_ms=500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    
    assert result["qa_completed"] is True
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN
    assert len(result["qa_sessions"]) == 1
    assert result["qa_sessions"][0].ai_confidence == 0.92


@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_loops_on_low_confidence(mock_llm):
    """Low confidence should loop back for more questions."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_LOW_CONFIDENCE,
        input_tokens=100,
        output_tokens=80,
        cost_usd=0.01,
        trace_name="qa_interaction",
        model_id="test-model",
        latency_ms=500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    
    assert result["qa_completed"] is False
    assert result["current_stage"] == WorkflowStage.QA_INTERACTION
    assert len(result["qa_sessions"]) == 1
    assert len(result["qa_sessions"][0].questions) == 1


@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_force_proceeds_on_max_iterations(mock_llm):
    """Should force-proceed after max iterations even with low confidence."""
    mock_llm.return_value = LLMResponse(
        content=MOCK_LOW_CONFIDENCE,
        input_tokens=100,
        output_tokens=80,
        cost_usd=0.01,
        trace_name="qa_interaction",
        model_id="test-model",
        latency_ms=500,
    )
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    state["qa_iteration_count"] = 2  # Already at max (0, 1, 2)
    result = qa_interaction_node(state)
    
    assert result["qa_completed"] is True  # Force-proceed
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_SPEC_GEN


@patch("src.graph.nodes.qa_interaction.call_llm")
def test_qa_interaction_handles_llm_failure(mock_llm):
    """LLM failure should return FAILED status."""
    mock_llm.side_effect = RuntimeError("Bedrock connection failed")
    state = create_initial_state("Test login", DUMMY_CONTEXT, "team", 0.85)
    result = qa_interaction_node(state)
    
    assert result["workflow_status"] == WorkflowStatus.FAILED
    assert "error_message" in result
    assert result["current_stage"] == WorkflowStage.FAILED