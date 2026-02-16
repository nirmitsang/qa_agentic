# src/graph/nodes/requirements_spec_gen.py
"""
Requirements Spec Generation node - generates test requirements document.
"""

import logging
from src.graph.state import AgentState, WorkflowStage

logger = logging.getLogger(__name__)


def requirements_spec_gen_node(state: AgentState) -> dict:
    """
    Requirements Spec Generation stub.
    """
    logger.info("STUB: requirements_spec_gen_node executing")
    
    # TODO: Implement in Phase 6
    
    return {
        "current_stage": WorkflowStage.JUDGE_REQUIREMENTS,
        "requirements_spec_content": "STUB SPEC",
    }