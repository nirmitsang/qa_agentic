"""
Reporting Node - V2 Stub
Generates final QA reports and metrics.
"""

import logging

from src.graph.state import AgentState, WorkflowStage, WorkflowStatus

logger = logging.getLogger(__name__)


def reporting_node(state: AgentState) -> dict:
    """
    Generate final QA report.

    V2 Implementation will:
    - Aggregate all artifacts
    - Generate HTML report
    - Calculate metrics (coverage, pass rate)
    - Store in S3
    - Send notifications

    Args:
        state: Current agent state

    Returns:
        Partial state dict with report and completion status
    """
    # TODO: V2 - Implement report generation
    logger.info(
        "STUB: Would generate final HTML report. V2 implementation."
    )
    return {
        "final_report_content": None,
        "current_stage": WorkflowStage.COMPLETED,
        "workflow_status": WorkflowStatus.COMPLETED,
    }