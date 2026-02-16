"""
Human Review Code Node — Gate #5 (Test Script Approval - Final Gate).
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes.human_review_spec import _human_review_base

logger = logging.getLogger(__name__)


def human_review_code_node(state: AgentState) -> dict:
    """
    Gate #5 — Test Script Approval (Final Gate).
    
    Pauses graph and waits for human to:
    - APPROVE → END (workflow complete)
    - REJECT → Regenerate script
    - EDIT → Store edited script and END
    
    Reads:
        - script_content
        - current_script_version
        - judge_code_evaluation
    
    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage.COMPLETED or WorkflowStage.SCRIPTING)
        - script_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Code node executing (Gate #5 - Final)")
    
    return _human_review_base(
        state=state,
        gate_name="code",
        document_content_key="script_content",
        document_version_key="current_script_version",
        approve_stage=WorkflowStage.COMPLETED,
        reject_stage=WorkflowStage.SCRIPTING,
    )