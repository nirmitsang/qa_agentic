"""
Judge Code Node — Evaluates generated test script quality.

Assesses the test script for plan adherence, code quality, test coverage,
framework correctness, and maintainability.
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes._judge_base import run_judge
from src.agents.prompts.judge_code_prompt import (
    JUDGE_CODE_SYSTEM_PROMPT,
    JUDGE_CODE_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def judge_code_node(state: AgentState) -> dict:
    """
    Evaluate test script quality.
    
    Reads:
        - script_content
        - code_plan_content (for plan adherence check)
        - gherkin_content
        - team_context.framework_type
        - script_iteration_count
        - max_judge_iterations
    
    Returns:
        - judge_code_evaluation (JudgeEvaluation)
        - current_stage (WorkflowStage)
    
    Routes:
        - PASS → HUMAN_REVIEW_CODE
        - FAIL → SCRIPTING (regenerate with feedback)
        - NEEDS_HUMAN → HUMAN_REVIEW_CODE
    """
    logger.info("Judge Code node executing")
    
    # Read state
    script_content = state.get("script_content", "")
    code_plan_content = state.get("code_plan_content", "")
    gherkin_content = state.get("gherkin_content", "")
    team_context = state.get("team_context")
    framework_type = team_context.framework_type.value if team_context else "unknown"
    iteration_count = state.get("script_iteration_count", 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    # Build user prompt
    user_prompt = JUDGE_CODE_USER_PROMPT_TEMPLATE.format(
        script_content=script_content,
        code_plan_content=code_plan_content,
        gherkin_content=gherkin_content,
        framework_type=framework_type,
        iteration=iteration_count,
        max_iterations=max_iterations,
        is_final_iteration=is_final_iteration,
    )
    
    # Call shared judge base
    return run_judge(
        state=state,
        system_prompt=JUDGE_CODE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name="judge_code",
        failure_stage=WorkflowStage.SCRIPTING,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_CODE,
        pass_stage=WorkflowStage.HUMAN_REVIEW_CODE,
        iteration_count_key="script_iteration_count",
        evaluation_key="judge_code_evaluation",
    )