"""
Judge Test Cases Node — Evaluates Gherkin test case quality.

Assesses Gherkin scenarios for strategy traceability, step quality,
coverage, and completeness.
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes._judge_base import run_judge
from src.agents.prompts.judge_test_cases_prompt import (
    JUDGE_TEST_CASES_SYSTEM_PROMPT,
    JUDGE_TEST_CASES_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def judge_test_cases_node(state: AgentState) -> dict:
    """
    Evaluate Gherkin test case quality.
    
    Reads:
        - gherkin_content
        - strategy_content
        - test_case_iteration_count
        - max_judge_iterations
    
    Returns:
        - judge_test_cases_evaluation (JudgeEvaluation)
        - current_stage (WorkflowStage)
    
    Routes:
        - PASS → HUMAN_REVIEW_TEST_CASES
        - FAIL → TEST_CASE_GENERATION (regenerate with feedback)
        - NEEDS_HUMAN → HUMAN_REVIEW_TEST_CASES
    """
    logger.info("Judge Test Cases node executing")
    
    # Read state
    gherkin_content = state.get("gherkin_content", "")
    strategy_content = state.get("strategy_content", "")
    iteration_count = state.get("test_case_iteration_count", 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    # Build user prompt
    user_prompt = JUDGE_TEST_CASES_USER_PROMPT_TEMPLATE.format(
        gherkin_content=gherkin_content,
        strategy_content=strategy_content,
        iteration=iteration_count,
        max_iterations=max_iterations,
        is_final_iteration=is_final_iteration,
    )
    
    # Call shared judge base
    return run_judge(
        state=state,
        system_prompt=JUDGE_TEST_CASES_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name="judge_test_cases",
        failure_stage=WorkflowStage.TEST_CASE_GENERATION,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_TEST_CASES,
        pass_stage=WorkflowStage.HUMAN_REVIEW_TEST_CASES,
        iteration_count_key="test_case_iteration_count",
        evaluation_key="judge_test_cases_evaluation",
    )