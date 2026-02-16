"""
Judge Requirements Node — Evaluates requirements specification quality.

This node assesses whether the generated requirements spec meets quality standards
using a 100-point rubric. Routes to human review on PASS/NEEDS_HUMAN, or back to
the generator on FAIL.
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes._judge_base import run_judge
from src.agents.prompts.judge_requirements_prompt import (
    JUDGE_REQUIREMENTS_SYSTEM_PROMPT,
    JUDGE_REQUIREMENTS_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def judge_requirements_node(state: AgentState) -> dict:
    """
    Evaluate requirements specification quality.
    
    Reads:
        - requirements_spec_content
        - raw_input
        - requirements_iteration_count
        - max_judge_iterations
    
    Returns:
        - judge_requirements_evaluation (JudgeEvaluation)
        - current_stage (WorkflowStage)
    
    Routes:
        - PASS → HUMAN_REVIEW_SPEC
        - FAIL → REQUIREMENTS_SPEC_GEN (regenerate with feedback)
        - NEEDS_HUMAN → HUMAN_REVIEW_SPEC
    """
    logger.info("Judge Requirements node executing")
    
    # Read state
    requirements_spec_content = state.get("requirements_spec_content", "")
    raw_input = state.get("raw_input", "")
    iteration_count = state.get("requirements_iteration_count", 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    # Build user prompt
    user_prompt = JUDGE_REQUIREMENTS_USER_PROMPT_TEMPLATE.format(
        requirements_spec_content=requirements_spec_content,
        raw_input=raw_input,
        iteration=iteration_count,
        max_iterations=max_iterations,
        is_final_iteration=is_final_iteration,
    )
    
    # Call shared judge base
    return run_judge(
        state=state,
        system_prompt=JUDGE_REQUIREMENTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name="judge_requirements",
        failure_stage=WorkflowStage.REQUIREMENTS_SPEC_GEN,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        pass_stage=WorkflowStage.HUMAN_REVIEW_SPEC,
        iteration_count_key="requirements_iteration_count",
        evaluation_key="judge_requirements_evaluation",
    )