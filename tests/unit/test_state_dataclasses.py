# tests/unit/test_state_dataclasses.py
from datetime import datetime
from src.graph.state import (
    Question, QASession, DocumentVersion, ApprovalGate,
    JudgeEvaluation, TeamContext, JudgeResult, FrameworkType
)

def test_question_instantiation():
    q = Question(id="Q1", text="What is the auth mechanism?", category="auth")
    assert q.is_required is True

def test_document_version_instantiation():
    dv = DocumentVersion(
        document_id="doc-001", workflow_id="wf-001",
        document_type="requirements_spec", version=1,
        content="# Spec", format="markdown", created_by="system"
    )
    assert dv.is_approved is False
    assert dv.storage_url is None  # V1: always None
    assert isinstance(dv.created_at, datetime)

def test_approval_gate_defaults():
    gate = ApprovalGate(gate_name="spec")
    assert gate.status == "pending"
    assert gate.reviewer is None

def test_judge_evaluation_instantiation():
    ev = JudgeEvaluation(
        score=85.0, result=JudgeResult.PASS, feedback="Good spec."
    )
    assert ev.issues == []
    assert ev.recommendations == []

def test_team_context_instantiation():
    ctx = TeamContext(
        tech_context_md="# Tech", codebase_map_md="# Codebase",
        framework_type=FrameworkType.API, conventions_summary="Use httpx."
    )
    assert ctx.framework_type == FrameworkType.API