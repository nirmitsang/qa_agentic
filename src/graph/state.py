"""
QA-GPT Core State Module

Defines all enums, dataclasses, and the AgentState TypedDict that flows through
the LangGraph pipeline. This is the single source of truth for state structure.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TypedDict, Optional
from uuid import uuid4


# ============================================================================
# ENUMS
# ============================================================================

class WorkflowStage(str, Enum):
    """All possible stages in the QA-GPT pipeline."""
    QA_INTERACTION = "qa_interaction"
    REQUIREMENTS_SPEC_GEN = "requirements_spec_gen"
    JUDGE_REQUIREMENTS = "judge_requirements"
    HUMAN_REVIEW_SPEC = "human_review_spec"
    STRATEGY = "strategy"
    JUDGE_STRATEGY = "judge_strategy"
    HUMAN_REVIEW_STRATEGY = "human_review_strategy"
    TEST_CASE_GENERATION = "test_case_generation"
    JUDGE_TEST_CASES = "judge_test_cases"
    HUMAN_REVIEW_TEST_CASES = "human_review_test_cases"
    CODE_STRUCTURE_PLANNING = "code_structure_planning"
    JUDGE_CODE_PLAN = "judge_code_plan"
    HUMAN_REVIEW_CODE_PLAN = "human_review_code_plan"
    SCRIPTING = "scripting"
    JUDGE_CODE = "judge_code"
    HUMAN_REVIEW_CODE = "human_review_code"
    EXECUTION = "execution"
    HEALING = "healing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class JudgeResult(str, Enum):
    """Possible outcomes from a judge evaluation."""
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class WorkflowStatus(str, Enum):
    """High-level workflow execution status."""
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FrameworkType(str, Enum):
    """Test framework category detected from context."""
    UI_E2E = "ui_e2e"
    API = "api"
    UNIT = "unit"
    UNKNOWN = "unknown"

# ============================================================================
# SUPPORTING DATACLASSES
# ============================================================================

@dataclass
class Question:
    """A single question in a QA session."""
    id: str
    text: str
    category: str
    is_required: bool = True


@dataclass
class QASession:
    """A complete Q&A interaction session."""
    session_id: str
    batch_number: int
    questions: list[Question]
    answers: dict
    ai_confidence: float
    status: str
    created_at: datetime


@dataclass
class DocumentVersion:
    """A versioned document in the pipeline."""
    document_id: str
    workflow_id: str
    document_type: str
    version: int
    content: str
    format: str
    created_by: str
    is_approved: bool = False
    storage_url: Optional[str] = None
    judge_score: Optional[float] = None
    judge_feedback: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ApprovalGate:
    """A human review gate in the workflow."""
    gate_name: str
    status: str = "pending"
    reviewer: Optional[str] = None
    feedback: Optional[str] = None
    document_version: Optional[DocumentVersion] = None
    reviewed_at: Optional[datetime] = None


@dataclass
class JudgeEvaluation:
    """Result of an AI judge evaluation."""
    score: float
    result: JudgeResult
    feedback: str
    issues: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TeamContext:
    """Team-specific context loaded from files or DB."""
    tech_context_md: str
    codebase_map_md: str
    framework_type: FrameworkType
    conventions_summary: str



# ============================================================================
# AGENTSTATE TYPEDDICT
# ============================================================================

class AgentState(TypedDict, total=False):
    """
    Complete state object passed between all LangGraph nodes.
    
    Uses total=False so all fields are optional - nodes use .get() with defaults.
    """
    # Identity
    workflow_id: str
    thread_id: str
    team_id: str
    trace_id: str
    workflow_status: WorkflowStatus
    current_stage: WorkflowStage
    error_message: Optional[str]
    
    # Context
    team_context: TeamContext
    
    # Input
    raw_input: str
    
    # Stage 1 — QA Interaction
    qa_sessions: list[QASession]
    qa_confidence: float
    qa_confidence_threshold: float
    qa_completed: bool
    qa_iteration_count: int
    
    # Stage 2-4 — Requirements
    requirements_spec_content: str
    current_requirements_spec_version: int
    requirements_spec_history: list[DocumentVersion]
    judge_requirements_evaluation: JudgeEvaluation
    requirements_iteration_count: int
    
    # Stage 4-7 — Strategy
    strategy_content: str
    current_strategy_version: int
    strategy_history: list[DocumentVersion]
    judge_strategy_evaluation: JudgeEvaluation
    strategy_iteration_count: int
    
    # Stage 6-10 — Gherkin
    gherkin_content: str
    current_test_cases_version: int
    test_cases_history: list[DocumentVersion]
    judge_test_cases_evaluation: JudgeEvaluation
    test_cases_iteration_count: int
    gherkin_validation_passed: bool
    
    # Stage 8-10 — Code Structure Plan
    code_plan_content: str
    current_code_plan_version: int
    code_plan_history: list[DocumentVersion]
    judge_code_plan_evaluation: JudgeEvaluation
    code_plan_iteration_count: int
    
    # Stage 10-12 — Script
    script_content: str
    script_filename: str
    current_script_version: int
    script_history: list[DocumentVersion]
    judge_code_evaluation: JudgeEvaluation
    script_iteration_count: int
    
    # Gates
    approval_gates: dict[str, ApprovalGate]
    human_feedback: Optional[str]
    human_guidance: Optional[str]
    
    # V2 stubs
    execution_result: Optional[dict]
    healing_attempts: int
    final_report_content: Optional[str]
    
    # Cost tracking
    accumulated_cost_usd: float
    
    # Judge configuration
    max_judge_iterations: int


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_initial_state(
    raw_input: str,
    team_context: TeamContext,
    team_id: str,
    qa_confidence_threshold: float
) -> AgentState:
    """
    Create a fresh AgentState with all required fields initialized.
    
    Args:
        raw_input: User's natural language feature description
        team_context: Loaded team context (tech stack, codebase map)
        team_id: Team identifier
        qa_confidence_threshold: Confidence threshold for triggering Q&A
        
    Returns:
        Fully initialized AgentState ready for the pipeline
    """
    workflow_id = str(uuid4())
    thread_id = str(uuid4())
    trace_id = str(uuid4())
    
    return AgentState(
        # Identity
        workflow_id=workflow_id,
        thread_id=thread_id,
        team_id=team_id,
        trace_id=trace_id,
        workflow_status=WorkflowStatus.RUNNING,
        current_stage=WorkflowStage.QA_INTERACTION,
        error_message=None,
        
        # Context
        team_context=team_context,
        
        # Input
        raw_input=raw_input,
        
        # Stage 1 — QA Interaction
        qa_sessions=[],
        qa_confidence=0.0,
        qa_confidence_threshold=qa_confidence_threshold,
        qa_completed=False,
        qa_iteration_count=0,
        
        # Stage 2-4 — Requirements
        requirements_spec_content="",
        current_requirements_spec_version=0,
        requirements_spec_history=[],
        requirements_iteration_count=0,
        
        # Stage 4-7 — Strategy
        strategy_content="",
        current_strategy_version=0,
        strategy_history=[],
        strategy_iteration_count=0,
        
        # Stage 6-10 — Gherkin
        gherkin_content="",
        current_test_cases_version=0,
        test_cases_history=[],
        test_cases_iteration_count=0,
        gherkin_validation_passed=False,
        
        # Stage 8-10 — Code Structure Plan
        code_plan_content="",
        current_code_plan_version=0,
        code_plan_history=[],
        code_plan_iteration_count=0,
        
        # Stage 10-12 — Script
        script_content="",
        script_filename="",
        current_script_version=0,
        script_history=[],
        script_iteration_count=0,
        
        # Gates - Pre-populate all 5 approval gates
        approval_gates={
            "spec": ApprovalGate(gate_name="spec"),
            "strategy": ApprovalGate(gate_name="strategy"),
            "test_cases": ApprovalGate(gate_name="test_cases"),
            "code_plan": ApprovalGate(gate_name="code_plan"),
            "code": ApprovalGate(gate_name="code"),
        },
        human_feedback=None,
        human_guidance=None,
        
        # V2 stubs
        execution_result=None,
        healing_attempts=0,
        final_report_content=None,
        
        # Cost tracking
        accumulated_cost_usd=0.0,
    )