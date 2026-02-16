"""
Human Review Code Plan Node — Gate #4 (Code Structure Plan Approval).
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes.human_review_spec import _human_review_base

logger = logging.getLogger(__name__)


def human_review_code_plan_node(state: AgentState) -> dict:
    """
    Gate #4 — Code Structure Plan Approval.
    
    Pauses graph and waits for human to:
    - APPROVE → Test script generation
    - REJECT → Regenerate code plan
    - EDIT → Store edited plan and proceed to scripting
    
    Reads:
        - code_plan_content
        - current_code_plan_version
        - judge_code_plan_evaluation
    
    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage)
        - code_plan_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Code Plan node executing (Gate #4)")
    
    return _human_review_base(
        state=state,
        gate_name="code_plan",
        document_content_key="code_plan_content",
        document_version_key="current_code_plan_version",
        approve_stage=WorkflowStage.SCRIPTING,
        reject_stage=WorkflowStage.CODE_STRUCTURE_PLANNING,
    )