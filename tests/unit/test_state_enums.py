# tests/unit/test_state_enums.py
from src.graph.state import WorkflowStage, JudgeResult, WorkflowStatus, FrameworkType

def test_workflow_stage_values():
    assert WorkflowStage.QA_INTERACTION.value == "qa_interaction"
    assert WorkflowStage.CODE_STRUCTURE_PLANNING.value == "code_structure_planning"
    assert WorkflowStage.COMPLETED.value == "completed"
    assert len(WorkflowStage) == 21

def test_judge_result_values():
    assert JudgeResult.PASS.value == "PASS"
    assert JudgeResult.NEEDS_HUMAN.value == "NEEDS_HUMAN"
    assert len(JudgeResult) == 3

def test_framework_type_values():
    assert FrameworkType.UI_E2E.value == "ui_e2e"
    assert FrameworkType.UNKNOWN.value == "unknown"

def test_enums_are_str_subclass():
    """Enums must be str subclasses for LangGraph state serialisation."""
    assert isinstance(WorkflowStage.QA_INTERACTION, str)
    assert isinstance(JudgeResult.PASS, str)