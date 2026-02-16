# src/graph/nodes/strategy.py
"""
Strategy node - generates test strategy document.
"""

import logging
from src.graph.state import AgentState, WorkflowStage

logger = logging.getLogger(__name__)


def strategy_node(state: AgentState) -> dict:
    """
    Strategy stub.
    """
    logger.info("STUB: strategy_node executing")
    
    # TODO: Implement in Phase 6
    
    return {
        "current_stage": WorkflowStage.JUDGE_STRATEGY,
        "strategy_content": "STUB STRATEGY",
    }