"""
Human Review Strategy Node — Gate #2 (Test Strategy Approval).
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes.human_review_spec import _human_review_base

logger = logging.getLogger(__name__)


def human_review_strategy_node(state: AgentState) -> dict:
    """
    Gate #2 — Test Strategy Approval.
    
    Pauses graph and waits for human to:
    - APPROVE → Test case generation
    - REJECT → Regenerate strategy
    - EDIT → Store edited strategy and proceed to test cases
    
    Reads:
        - strategy_content
        - current_strategy_version
        - judge_strategy_evaluation
    
    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage)
        - strategy_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Strategy node executing (Gate #2)")
    
    return _human_review_base(
        state=state,
        gate_name="strategy",
        document_content_key="strategy_content",
        document_version_key="current_strategy_version",
        approve_stage=WorkflowStage.TEST_CASE_GENERATION,
        reject_stage=WorkflowStage.STRATEGY,
    )