# tests/integration/test_full_pipeline.py
"""
Full Pipeline Integration Test — Phase 11 (Task 11.1)

Tests the complete graph execution from START through multiple stages.

Two test categories:
1. Unit-level (no LLM calls) — state creation and graph smoke tests
2. Integration (real LLM calls) — full pipeline to first interrupt gate

Run unit tests only:
    pytest tests/integration/test_full_pipeline.py -v -k "not integration"

Run integration tests (requires credentials):
    pytest tests/integration/test_full_pipeline.py -m integration -v -s
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.graph.builder import qa_graph
from src.graph.state import (
    create_initial_state,
    AgentState,
    WorkflowStage,
    WorkflowStatus,
    TeamContext,
    FrameworkType,
)
from src.knowledge.retrieval.context_fetcher import fetch_context
from src.config.settings import settings
from src.agents.llm_client import LLMResponse


# ===========================================================================
# FIXTURES
# ===========================================================================

DUMMY_CONTEXT = TeamContext(
    tech_context_md="We use Playwright for browser e2e testing.",
    codebase_map_md="# Codebase Map\n## Existing Utils\n```python\ndef login(): pass\n```",
    framework_type=FrameworkType.UI_E2E,
    conventions_summary="PEP8, use httpx for API calls.",
)

# Mock LLM responses matching the actual JSON schemas used by nodes
MOCK_QA_HIGH_CONFIDENCE = json.dumps({
    "ai_confidence": 0.92,
    "can_proceed": True,
    "framework_type": "ui_e2e",
    "questions": [],
})

MOCK_REQUIREMENTS_SPEC = """# Requirements Specification

## 1. Overview
Test the login feature for the web application.

## 2. Functional Requirements
- FR-001: User can login with valid email and password
- FR-002: User sees error on invalid credentials

## 3. Non-Functional Requirements
- NFR-001: Login page loads within 2 seconds

## 4. Acceptance Criteria
- Given a valid user, When they enter credentials, Then they see the dashboard

## 5. Edge Cases & Boundary Conditions
- Empty fields, SQL injection attempts

## 6. Out of Scope
- Social login

## 7. Test Data Requirements
- Valid user: test@example.com / password123

## 8. Dependencies & Assumptions
- Database is seeded with test user

## 9. Risk Assessment
- LOW: Standard login flow
"""

MOCK_JUDGE_PASS = json.dumps({
    "score": 85,
    "result": "PASS",
    "feedback": "Requirements are comprehensive and testable.",
    "issues": [],
    "recommendations": ["Consider adding more edge cases."],
    "human_question": None,
})

MOCK_JUDGE_FAIL = json.dumps({
    "score": 55,
    "result": "FAIL",
    "feedback": "Missing several required sections.",
    "issues": [{"type": "missing_section", "description": "No risk assessment", "severity": "HIGH"}],
    "recommendations": ["Add risk assessment section."],
    "human_question": None,
})


# ===========================================================================
# UNIT TESTS (no LLM calls)
# ===========================================================================

def test_graph_compiles():
    """The graph can be imported and is compiled (not None)."""
    assert qa_graph is not None


def test_graph_has_invoke_methods():
    """Graph has the standard LangGraph interface methods."""
    assert hasattr(qa_graph, "invoke")
    assert hasattr(qa_graph, "stream")


def test_graph_has_correct_node_count():
    """Graph has all 17 expected nodes (16 pipeline + __start__)."""
    graph_nodes = list(qa_graph.nodes.keys())
    # 16 pipeline nodes + __start__
    assert len(graph_nodes) >= 17, f"Expected 17+ nodes, got {len(graph_nodes)}: {graph_nodes}"


def test_initial_state_flows_into_graph():
    """Minimal smoke test: graph accepts initial state structure."""
    team_context = fetch_context(team_id="local_team")
    initial_state = create_initial_state(
        raw_input="Test the user login feature.",
        team_context=team_context,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    assert initial_state["workflow_id"] is not None
    assert initial_state["qa_sessions"] == []
    assert len(initial_state["approval_gates"]) == 5
    assert initial_state["current_stage"] == WorkflowStage.QA_INTERACTION
    assert initial_state["workflow_status"] == WorkflowStatus.RUNNING


def test_graph_expected_nodes_present():
    """Verify all expected node names are registered in the graph."""
    expected_nodes = [
        "qa_interaction",
        "requirements_spec_gen",
        "judge_requirements",
        "human_review_spec",
        "strategy",
        "judge_strategy",
        "human_review_strategy",
        "test_case_generation",
        "judge_test_cases",
        "human_review_test_cases",
        "code_structure_planning",
        "judge_code_plan",
        "human_review_code_plan",
        "scripting",
        "judge_code",
        "human_review_code",
    ]
    graph_nodes = list(qa_graph.nodes.keys())
    for node in expected_nodes:
        assert node in graph_nodes, f"Missing node: {node}"


# ===========================================================================
# MOCKED PIPELINE TESTS (no real LLM calls, tests graph flow)
# ===========================================================================

@patch("src.graph.nodes.qa_interaction.call_llm")
@patch("src.graph.nodes.requirements_spec_gen.call_llm")
@patch("src.graph.nodes._judge_base.call_llm")
def test_mocked_pipeline_reaches_first_gate(mock_judge_llm, mock_spec_llm, mock_qa_llm):
    """
    Mocked pipeline test: QA → Spec Gen → Judge → Human Review Spec (interrupt).
    
    Uses mocked LLM responses to verify the graph flow reaches Gate #1
    without needing real LLM credentials.
    """
    # Set up mock responses
    mock_qa_llm.return_value = LLMResponse(
        content=MOCK_QA_HIGH_CONFIDENCE,
        input_tokens=100, output_tokens=50, cost_usd=0.001,
        trace_name="qa_interaction", model_id="test-model", latency_ms=100,
    )
    mock_spec_llm.return_value = LLMResponse(
        content=MOCK_REQUIREMENTS_SPEC,
        input_tokens=200, output_tokens=300, cost_usd=0.003,
        trace_name="requirements_spec_gen", model_id="test-model", latency_ms=200,
    )
    mock_judge_llm.return_value = LLMResponse(
        content=MOCK_JUDGE_PASS,
        input_tokens=150, output_tokens=75, cost_usd=0.001,
        trace_name="judge_requirements", model_id="test-model", latency_ms=100,
    )

    # Create initial state
    initial_state = create_initial_state(
        raw_input="Test the login page with email/password login.",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}

    # Stream graph execution — should reach interrupt at Gate #1
    final_state = None
    interrupted = False
    for state_snapshot in qa_graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = state_snapshot

    # After stream completes (interrupt causes stream to end), check state
    assert final_state is not None
    assert mock_qa_llm.called, "QA Interaction LLM was not called"
    assert mock_spec_llm.called, "Requirements Spec Gen LLM was not called"
    assert mock_judge_llm.called, "Judge Requirements LLM was not called"

    # The graph should have produced a requirements spec
    assert len(final_state.get("requirements_spec_content", "")) > 50
    assert final_state.get("current_requirements_spec_version", 0) >= 1

    # Judge evaluation should be stored
    judge_eval = final_state.get("judge_requirements_evaluation")
    assert judge_eval is not None
    assert judge_eval.score == 85

    # Should have reached human review spec stage (interrupt pauses here)
    assert final_state.get("current_stage") == WorkflowStage.HUMAN_REVIEW_SPEC


@patch("src.graph.nodes.qa_interaction.call_llm")
@patch("src.graph.nodes.requirements_spec_gen.call_llm")
@patch("src.graph.nodes._judge_base.call_llm")
def test_mocked_pipeline_judge_fail_triggers_retry(mock_judge_llm, mock_spec_llm, mock_qa_llm):
    """
    Test that a FAIL judge result routes back to regeneration.
    
    Flow: QA → Spec Gen → Judge (FAIL) → Spec Gen (retry) → Judge (PASS) → Gate #1
    """
    # QA always passes
    mock_qa_llm.return_value = LLMResponse(
        content=MOCK_QA_HIGH_CONFIDENCE,
        input_tokens=100, output_tokens=50, cost_usd=0.001,
        trace_name="qa_interaction", model_id="test-model", latency_ms=100,
    )
    # Spec gen always returns content
    mock_spec_llm.return_value = LLMResponse(
        content=MOCK_REQUIREMENTS_SPEC,
        input_tokens=200, output_tokens=300, cost_usd=0.003,
        trace_name="requirements_spec_gen", model_id="test-model", latency_ms=200,
    )
    # Judge: first FAIL, then PASS on retry
    mock_judge_llm.side_effect = [
        LLMResponse(
            content=MOCK_JUDGE_FAIL,
            input_tokens=150, output_tokens=75, cost_usd=0.001,
            trace_name="judge_requirements", model_id="test-model", latency_ms=100,
        ),
        LLMResponse(
            content=MOCK_JUDGE_PASS,
            input_tokens=150, output_tokens=75, cost_usd=0.001,
            trace_name="judge_requirements", model_id="test-model", latency_ms=100,
        ),
    ]

    initial_state = create_initial_state(
        raw_input="Test login feature.",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}

    final_state = None
    for state_snapshot in qa_graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = state_snapshot

    assert final_state is not None
    # Spec gen should have been called twice (initial + retry after FAIL)
    assert mock_spec_llm.call_count == 2, f"Expected 2 spec gen calls, got {mock_spec_llm.call_count}"
    # Judge should have been called twice (FAIL + PASS)
    assert mock_judge_llm.call_count == 2, f"Expected 2 judge calls, got {mock_judge_llm.call_count}"
    # Eventually reaches human review
    assert final_state.get("current_stage") == WorkflowStage.HUMAN_REVIEW_SPEC


@patch("src.graph.nodes.qa_interaction.call_llm")
def test_mocked_pipeline_qa_low_confidence_loops(mock_qa_llm):
    """
    Test QA interaction loop: low confidence → graph stays at qa_interaction.
    
    When confidence < threshold, the node sets qa_completed=False and
    current_stage=QA_INTERACTION. The graph will loop back, but since
    the mock returns the same low-confidence response, it eventually
    force-proceeds after 3 iterations (max batches).
    """
    mock_qa_llm.return_value = LLMResponse(
        content=json.dumps({
            "ai_confidence": 0.60,
            "can_proceed": False,
            "framework_type": "ui_e2e",
            "questions": [
                "What auth method does the app use?",
                "Which browser should we target?",
            ],
        }),
        input_tokens=100, output_tokens=80, cost_usd=0.001,
        trace_name="qa_interaction", model_id="test-model", latency_ms=100,
    )

    initial_state = create_initial_state(
        raw_input="Test login.",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}

    final_state = None
    for state_snapshot in qa_graph.stream(initial_state, config=config, stream_mode="values"):
        final_state = state_snapshot

    assert final_state is not None
    # After 3 iterations of low confidence, QA force-proceeds
    # The node stores QASession objects with questions from the LLM JSON
    sessions = final_state.get("qa_sessions", [])
    assert len(sessions) >= 1
    # Each session stores the raw questions from the LLM response
    assert len(sessions[0].questions) == 2
    # Eventually QA completes (force-proceed after max iterations)
    assert final_state.get("qa_completed") is True
    assert final_state.get("qa_iteration_count") == 3


# ===========================================================================
# INTEGRATION TESTS (require real LLM credentials in .env)
# ===========================================================================

@pytest.mark.integration
def test_pipeline_reaches_first_gate():
    """
    Full pipeline test: START → QA Interaction → Spec Gen → Judge → Gate #1.
    Requires real LLM credentials in .env.
    """
    team_context = fetch_context(team_id=settings.team_id)
    initial_state = create_initial_state(
        raw_input=(
            "Create API tests for POST /api/v1/login. "
            "Returns 200 with JWT on success, 401 on wrong credentials, "
            "422 on missing fields."
        ),
        team_context=team_context,
        team_id=settings.team_id,
        qa_confidence_threshold=settings.qa_confidence_threshold,
    )
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}

    final_state = None
    stages_seen = []
    try:
        for state_snapshot in qa_graph.stream(
            initial_state, config=config, stream_mode="values"
        ):
            final_state = state_snapshot
            stage = state_snapshot.get("current_stage")
            if stage:
                stages_seen.append(str(stage))
                print(f"  Stage: {stage}")
    except Exception as e:
        # LangGraph raises GraphInterrupt when interrupt() is called
        if "GraphInterrupt" in type(e).__name__ or "interrupt" in str(e).lower():
            pytest.skip(f"Graph correctly interrupted at gate (expected): {e}")
        raise

    # If we reach here, the graph advanced without error
    assert final_state is not None
    assert len(stages_seen) >= 3, f"Expected at least 3 stages, saw: {stages_seen}"
    assert "requirements_spec_content" in final_state
    assert len(final_state.get("requirements_spec_content", "")) > 100
    print(f"\n✅ Stages traversed: {' → '.join(stages_seen)}")
    print(f"✅ Spec length: {len(final_state.get('requirements_spec_content', ''))}")
    print(f"✅ Accumulated cost: ${final_state.get('accumulated_cost_usd', 0):.4f}")