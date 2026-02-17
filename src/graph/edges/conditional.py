# src/graph/edges/conditional.py
"""
Conditional routing functions for the QA-GPT graph.
Each function reads current_stage from state and returns its string value.
"""

import logging
from langgraph.graph import END
from src.graph.state import AgentState, WorkflowStage

logger = logging.getLogger(__name__)


def _safe_get_stage_value(state: AgentState) -> str:
    """
    Safely extract current_stage value from state.
    
    Returns the stage's .value string, or END if stage is FAILED/missing
    so the graph terminates cleanly.
    """
    current_stage = state.get("current_stage", WorkflowStage.FAILED)
    
    # If it's a WorkflowStage enum, check for FAILED → END
    if isinstance(current_stage, WorkflowStage):
        if current_stage == WorkflowStage.FAILED:
            return END
        return current_stage.value
    
    # If it's already a string, check for "failed" → END
    if isinstance(current_stage, str):
        if current_stage == WorkflowStage.FAILED.value:
            return END
        return current_stage
    
    # Fallback to END (terminate graph)
    return END


# ============================================================================
# ROUTING FUNCTIONS (11 total)
# ============================================================================

def route_after_qa_interaction(state: AgentState) -> str:
    """Route after QA Interaction node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_qa_interaction → {result}")
    return result


def route_after_judge_requirements(state: AgentState) -> str:
    """Route after Judge Requirements node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_judge_requirements → {result}")
    return result


def route_after_human_review_spec(state: AgentState) -> str:
    """Route after Human Review Spec node (Gate #1)."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_human_review_spec → {result}")
    return result


def route_after_judge_strategy(state: AgentState) -> str:
    """Route after Judge Strategy node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_judge_strategy → {result}")
    return result


def route_after_human_review_strategy(state: AgentState) -> str:
    """Route after Human Review Strategy node (Gate #2)."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_human_review_strategy → {result}")
    return result


def route_after_judge_test_cases(state: AgentState) -> str:
    """Route after Judge Test Cases node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_judge_test_cases → {result}")
    return result


def route_after_human_review_test_cases(state: AgentState) -> str:
    """Route after Human Review Test Cases node (Gate #3)."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_human_review_test_cases → {result}")
    return result


def route_after_judge_code_plan(state: AgentState) -> str:
    """Route after Judge Code Plan node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_judge_code_plan → {result}")
    return result


def route_after_human_review_code_plan(state: AgentState) -> str:
    """Route after Human Review Code Plan node (Gate #4)."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_human_review_code_plan → {result}")
    return result


def route_after_judge_code(state: AgentState) -> str:
    """Route after Judge Code node."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_judge_code → {result}")
    return result


def route_after_human_review_code(state: AgentState) -> str:
    """Route after Human Review Code node (Gate #5 - final)."""
    result = _safe_get_stage_value(state)
    logger.debug(f"route_after_human_review_code → {result}")
    return result