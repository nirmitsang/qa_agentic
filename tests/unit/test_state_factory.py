# tests/unit/test_state_factory.py
from src.graph.state import (
    create_initial_state, AgentState, WorkflowStatus, WorkflowStage,
    TeamContext, FrameworkType
)

DUMMY_CONTEXT = TeamContext(
    tech_context_md="# Tech Context", codebase_map_md="# Codebase Map",
    framework_type=FrameworkType.API, conventions_summary="Use httpx."
)

def test_create_initial_state_returns_agent_state():
    state = create_initial_state(
        raw_input="Test the login page",
        team_context=DUMMY_CONTEXT,
        team_id="local_team",
        qa_confidence_threshold=0.85
    )
    assert isinstance(state, dict)
    assert state["raw_input"] == "Test the login page"

def test_initial_state_has_uuids():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert len(state["workflow_id"]) > 0
    assert len(state["thread_id"]) > 0

def test_initial_state_list_fields_are_empty_lists():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert state["qa_sessions"] == []
    assert state["requirements_spec_history"] == []
    assert state["code_plan_history"] == []

def test_initial_state_has_all_five_approval_gates():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    gates = state["approval_gates"]
    assert set(gates.keys()) == {"spec", "strategy", "test_cases", "code_plan", "code"}
    for gate in gates.values():
        assert gate.status == "pending"

def test_initial_state_workflow_status():
    state = create_initial_state("input", DUMMY_CONTEXT, "team", 0.85)
    assert state["workflow_status"] == WorkflowStatus.RUNNING
    assert state["current_stage"] == WorkflowStage.QA_INTERACTION