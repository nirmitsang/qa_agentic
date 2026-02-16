"""
Judge Code Plan Node — Evaluates code structure plan quality.

SPECIAL ROUTING: Unlike other judges, both PASS and most FAIL results route to
human review. Only critical issues (duplicate utilities, convention violations)
trigger regeneration.
"""

import logging

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes._judge_base import run_judge
from src.agents.prompts.judge_code_plan_prompt import (
    JUDGE_CODE_PLAN_SYSTEM_PROMPT,
    JUDGE_CODE_PLAN_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def judge_code_plan_node(state: AgentState) -> dict:
    """
    Evaluate code structure plan quality.
    
    SPECIAL ROUTING per PRD Section 12.4:
    - PASS → HUMAN_REVIEW_CODE_PLAN (always)
    - FAIL with critical issues → CODE_STRUCTURE_PLANNING (regenerate)
    - FAIL with minor issues → HUMAN_REVIEW_CODE_PLAN (inform human)
    - NEEDS_HUMAN → HUMAN_REVIEW_CODE_PLAN
    
    Critical issues are detected via validation_checks in the JSON response:
    - validation_checks.no_duplicate_utilities = False
    - validation_checks.follows_conventions = False
    
    Reads:
        - code_plan_content
        - gherkin_content
        - team_context (tech_context_md, codebase_map_md)
        - code_plan_iteration_count
        - max_judge_iterations
    
    Returns:
        - judge_code_plan_evaluation (JudgeEvaluation)
        - current_stage (WorkflowStage)
    """
    logger.info("Judge Code Plan node executing")
    
    # Read state
    code_plan_content = state.get("code_plan_content", "")
    gherkin_content = state.get("gherkin_content", "")
    team_context = state.get("team_context")
    tech_context_md = team_context.tech_context_md if team_context else ""
    codebase_map_md = team_context.codebase_map_md if team_context else ""
    iteration_count = state.get("code_plan_iteration_count", 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    # Build user prompt
    user_prompt = JUDGE_CODE_PLAN_USER_PROMPT_TEMPLATE.format(
        code_plan_content=code_plan_content,
        gherkin_content=gherkin_content,
        tech_context_md=tech_context_md,
        codebase_map_md=codebase_map_md,
        iteration=iteration_count,
        max_iterations=max_iterations,
        is_final_iteration=is_final_iteration,
    )
    
    # Call shared judge base
    # NOTE: The base function will handle standard routing, but we override below
    result = run_judge(
        state=state,
        system_prompt=JUDGE_CODE_PLAN_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        trace_name="judge_code_plan",
        failure_stage=WorkflowStage.CODE_STRUCTURE_PLANNING,
        human_review_stage=WorkflowStage.HUMAN_REVIEW_CODE_PLAN,
        pass_stage=WorkflowStage.HUMAN_REVIEW_CODE_PLAN,
        iteration_count_key="code_plan_iteration_count",
        evaluation_key="judge_code_plan_evaluation",
    )
    
    # SPECIAL ROUTING OVERRIDE for code plan
    # Check if this was a FAIL that should actually go to human review
    if "judge_code_plan_evaluation" in result:
        evaluation = result["judge_code_plan_evaluation"]
        
        # If FAIL, check for critical issues
        if result["current_stage"] == WorkflowStage.CODE_STRUCTURE_PLANNING:
            # Extract validation_checks from issues if present
            has_critical_issue = False
            
            for issue in evaluation.issues:
                # Check for critical keywords in issue descriptions
                description_lower = issue.get("description", "").lower()
                issue_type = issue.get("type", "").lower()
                
                if "duplicate" in description_lower or "duplicate" in issue_type:
                    has_critical_issue = True
                    logger.warning("Critical issue detected: duplicate utilities")
                    break
                if "convention" in description_lower and "violat" in description_lower:
                    has_critical_issue = True
                    logger.warning("Critical issue detected: convention violation")
                    break
            
            # If no critical issues, override to human review
            if not has_critical_issue:
                logger.info(
                    "Code plan FAIL has no critical issues. "
                    "Routing to human review instead of regeneration."
                )
                result["current_stage"] = WorkflowStage.HUMAN_REVIEW_CODE_PLAN
    
    return result