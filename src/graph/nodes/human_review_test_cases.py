"""
Human Review Test Cases Node — Gate #3 (Gherkin Test Cases Approval).
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes.human_review_spec import _human_review_base

logger = logging.getLogger(__name__)


def human_review_test_cases_node(state: AgentState) -> dict:
    """
    Gate #3 — Gherkin Test Cases Approval.
    
    Pauses graph and waits for human to:
    - APPROVE → Code structure planning
    - REJECT → Regenerate test cases
    - EDIT → Store edited Gherkin and proceed to code planning
    
    Reads:
        - gherkin_content
        - current_test_cases_version
        - judge_test_cases_evaluation
    
    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage)
        - gherkin_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Test Cases node executing (Gate #3)")
    
    return _human_review_base(
        state=state,
        gate_name="test_cases",
        document_content_key="gherkin_content",
        document_version_key="current_test_cases_version",
        approve_stage=WorkflowStage.CODE_STRUCTURE_PLANNING,
        reject_stage=WorkflowStage.TEST_CASE_GENERATION,
    )