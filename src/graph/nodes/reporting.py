# src/graph/nodes/reporting.py
"""
Reporting node - generates test execution report (V2 feature).
"""

import logging
from src.graph.state import AgentState, WorkflowStage

logger = logging.getLogger(__name__)


def reporting_node(state: AgentState) -> dict:
    """
    Reporting stub - V2 feature, not reachable in V1.
    """
    logger.info("STUB: reporting_node executing")
    
    # TODO: Implement in Phase 6 (V2)
    
    return {
        "current_stage": WorkflowStage.COMPLETED,
    }