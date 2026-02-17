"""
Human Review Spec Node — Gate #1 (Requirements Specification Approval).

This node pauses the graph using interrupt() and waits for human decision.
The _human_review_base() function implements shared logic for all 5 gates.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.types import interrupt

from src.graph.state import AgentState, WorkflowStage, ApprovalGate

logger = logging.getLogger(__name__)


def _human_review_base(
    state: AgentState,
    gate_name: str,
    document_content_key: str,
    document_version_key: str,
    approve_stage: WorkflowStage,
    reject_stage: WorkflowStage,
    extra_payload: dict | None = None,
) -> dict[str, Any]:
    """
    Shared human review logic for all 5 gates.
    
    This function:
    1. Builds interrupt payload with document content and judge feedback
    2. Calls interrupt() — graph pauses here until human responds
    3. Parses human decision (APPROVE/REJECT/EDIT)
    4. Updates approval_gates in state
    5. Routes to next stage based on decision
    
    Args:
        state: Current AgentState
        gate_name: Gate identifier ("spec", "strategy", "test_cases", "code_plan", "code")
        document_content_key: State key for document content (e.g., "requirements_spec_content")
        document_version_key: State key for version number (e.g., "current_requirements_spec_version")
        approve_stage: Where to route on APPROVE/EDIT
        reject_stage: Where to route on REJECT
    
    Returns:
        Partial state dict with approval gate update and routing decision
    """
    logger.info(f"Human Review Base: {gate_name} gate")
    
    # Get document content and metadata
    document_content = state.get(document_content_key, "")
    document_version = state.get(document_version_key, 1)
    
    # Get judge evaluation (may be None if this is a NEEDS_HUMAN route)
    judge_eval_key = f"judge_{gate_name}_evaluation" if gate_name != "spec" else "judge_requirements_evaluation"
    judge_evaluation = state.get(judge_eval_key)
    
    judge_score = judge_evaluation.score if judge_evaluation else None
    judge_feedback = judge_evaluation.feedback if judge_evaluation else "No judge feedback available."
    judge_result = judge_evaluation.result.value if judge_evaluation else "N/A"
    
    # Build interrupt payload
    payload = {
        "gate_name": gate_name,
        "document_content": document_content,
        "document_version": document_version,
        "judge_score": judge_score,
        "judge_feedback": judge_feedback,
        "judge_result": judge_result,
        "human_question": None,
    }
    
    # If judge evaluation has a human_question, include it
    if judge_evaluation and hasattr(judge_evaluation, "human_question"):
        # Note: human_question is not in the JudgeEvaluation dataclass from Phase 2,
        # but judges can include it in their JSON responses. We'll extract it from issues.
        pass  # For now, leave as None
    
    # Merge any extra payload items (e.g., file_tree for code_plan gate)
    if extra_payload:
        payload.update(extra_payload)
    
    logger.info(f"Interrupting for human review: {gate_name} (version {document_version})")
    
    # INTERRUPT — Graph pauses here until human responds
    human_response = interrupt(payload)
    
    logger.info(f"Human response received for {gate_name}: {human_response.get('decision')}")
    
    # Parse human decision
    decision = human_response.get("decision", "REJECT")  # Default to REJECT if missing
    feedback = human_response.get("feedback", "")
    edited_content = human_response.get("edited_content", "")
    
    # Update approval gate in state
    approval_gates = state.get("approval_gates", {})
    
    if decision == "APPROVE":
        # Mark gate as approved
        approval_gates[gate_name] = ApprovalGate(
            gate_name=gate_name,
            status="approved",
            reviewer="human",
            feedback=feedback,
            document_version=document_version,
            reviewed_at=datetime.now(timezone.utc),
        )
        next_stage = approve_stage
        logger.info(f"{gate_name} APPROVED → {next_stage.value}")
    
    elif decision == "EDIT":
        # Mark gate as approved with edited content
        approval_gates[gate_name] = ApprovalGate(
            gate_name=gate_name,
            status="approved",
            reviewer="human",
            feedback=f"Approved with edits: {feedback}",
            document_version=document_version,
            reviewed_at=datetime.now(timezone.utc),
        )
        next_stage = approve_stage
        logger.info(f"{gate_name} APPROVED (with edits) → {next_stage.value}")
        
        # Return edited content to update the document
        return {
            document_content_key: edited_content,
            "approval_gates": approval_gates,
            "current_stage": next_stage,
        }
    
    else:  # REJECT
        # Mark gate as rejected
        approval_gates[gate_name] = ApprovalGate(
            gate_name=gate_name,
            status="rejected",
            reviewer="human",
            feedback=feedback,
            document_version=document_version,
            reviewed_at=datetime.now(timezone.utc),
        )
        next_stage = reject_stage
        logger.info(f"{gate_name} REJECTED → {next_stage.value} (regenerate)")
        
        # Store feedback for regeneration
        return {
            "approval_gates": approval_gates,
            "human_feedback": feedback,
            "current_stage": next_stage,
        }
    
    # APPROVE case (no edits)
    return {
        "approval_gates": approval_gates,
        "current_stage": next_stage,
    }


def human_review_spec_node(state: AgentState) -> dict:
    """
    Gate #1 — Requirements Specification Approval.
    
    Pauses graph and waits for human to:
    - APPROVE → Strategy generation
    - REJECT → Regenerate spec
    - EDIT → Store edited spec and proceed to strategy
    
    Reads:
        - requirements_spec_content
        - current_requirements_spec_version
        - judge_requirements_evaluation
    
    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage)
        - requirements_spec_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Spec node executing (Gate #1)")
    
    return _human_review_base(
        state=state,
        gate_name="spec",
        document_content_key="requirements_spec_content",
        document_version_key="current_requirements_spec_version",
        approve_stage=WorkflowStage.STRATEGY,
        reject_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
    )