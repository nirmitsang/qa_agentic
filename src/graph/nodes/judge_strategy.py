"""
Judge Strategy Node — Evaluates test strategy quality.

Assesses the strategy document using a 100-point rubric covering coverage,
test case quality, risk assessment, and effort estimation.
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes._judge_base import run_judge
from src.agents.prompts.judge_strategy_prompt import (
    JUDGE_STRATEGY_SYSTEM_PROMPT,
    JUDGE_STRATEGY_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def judge_strategy_node(state: AgentState) -> dict:
    """
    Evaluate test strategy quality.
    
    Reads:
        - strategy_content
        - requirements_spec_content
        - strategy_iteration_count
        - max_judge_iterations
    
    Returns:
        - judge_strategy_evaluation (JudgeEvaluation)
        - current_stage (WorkflowStage)
    
    Routes:
        - PASS → HUMAN_REVIEW_STRATEGY
        - FAIL → STRATEGY (regenerate with feedback)
        - NEEDS_HUMAN → HUMAN_REVIEW_STRATEGY
    """
    logger.info("Judge Strategy node executing")
    
    # Read state
    strategy_content = state.get("strategy_content", "")
    requirements_spec_content = state.get("requirements_spec_content", "")
    iteration_count = state.get("strategy_iteration_count", 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    # Build user prompt
    user_prompt = JUDGE_STRATEGY_USER_PROMPT_TEMPLATE.format(
        strategy_content=strategy_content,
        requirements_spec_content=requirements_spec_content,
        iteration=iteration_count,
        max_iterations=max_iterations,
        is_final_iteration=is_final_iteration,
    )
    
    # Call shared judge base
    return run_judge(
        state=state,
        system_prompt=JUDGE_STRATEGY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name="judge_strategy",
        failure_stage=WorkflowStage.STRATEGY,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_STRATEGY,
        pass_stage=WorkflowStage.HUMAN_REVIEW_STRATEGY,
        iteration_count_key="strategy_iteration_count",
        evaluation_key="judge_strategy_evaluation",
    )