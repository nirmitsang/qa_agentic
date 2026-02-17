"""
Shared judge logic for all judge nodes.

This module contains the run_judge() function that implements the common pattern
for all 5 judge nodes in the QA-GPT pipeline. Each judge evaluates a document
and routes to: PASS (human review), FAIL (regenerate), or NEEDS_HUMAN (escalate).
"""

import logging
from typing import Any

from src.graph.state import (
    AgentState,
    WorkflowStage,
    WorkflowStatus,
    JudgeResult,
    JudgeEvaluation,
)
from src.agents.llm_client import call_llm, extract_json_from_response

logger = logging.getLogger(__name__)


def run_judge(
    state: AgentState,
    system_prompt: str,
    user_prompt: str,
    trace_name: str,
    failure_stage: WorkflowStage,
    human_review_stage: WorkflowStage,
    pass_stage: WorkflowStage,
    iteration_count_key: str,
    evaluation_key: str,
) -> dict[str, Any]:
    """
    Shared judge evaluation logic.
    
    This function is called by all 5 judge nodes. It:
    1. Calls the LLM with the provided prompts
    2. Parses the JSON response into a JudgeEvaluation dataclass
    3. Applies routing logic based on the judge's result
    4. Enforces the max iteration rule (FAIL → NEEDS_HUMAN on final iteration)
    
    Args:
        state: Current AgentState
        system_prompt: Judge system prompt (defines role and rubric)
        user_prompt: Judge user prompt (formatted with document content)
        trace_name: Trace identifier for observability
        failure_stage: Where to route on FAIL (the generator node)
        human_review_stage: Where to route on NEEDS_HUMAN or final iteration
        pass_stage: Where to route on PASS (typically human_review_stage)
        iteration_count_key: State key for iteration counter (e.g., "requirements_iteration_count")
        evaluation_key: State key for evaluation storage (e.g., "judge_requirements_evaluation")
    
    Returns:
        Partial state dict with evaluation and routing decision
    """
    logger.info(f"Running judge: {trace_name}")
    
    # Get iteration tracking
    iteration_count = state.get(iteration_count_key, 0)
    max_iterations = state.get("max_judge_iterations", 3)
    is_final_iteration = iteration_count >= (max_iterations - 1)
    
    logger.info(
        f"{trace_name}: iteration {iteration_count}/{max_iterations} "
        f"(final={is_final_iteration})"
    )
    
    try:
        # Call LLM
        response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            trace_name=trace_name,
            trace_id=state.get("trace_id"),
        )
        
        # Extract JSON from response
        result_json = extract_json_from_response(response.content)
        
        # Parse into JudgeEvaluation dataclass
        evaluation = JudgeEvaluation(
            score=result_json["score"],
            result=JudgeResult(result_json["result"]),
            feedback=result_json["feedback"],
            issues=result_json.get("issues", []),
            recommendations=result_json.get("recommendations", []),
        )
        
        logger.info(
            f"{trace_name} result: {evaluation.result.value} "
            f"(score: {evaluation.score}/100)"
        )
        
        # Apply max iteration override
        # On final iteration, FAIL becomes NEEDS_HUMAN (never loop forever)
        if is_final_iteration and evaluation.result == JudgeResult.FAIL:
            logger.warning(
                f"{trace_name}: Final iteration reached with FAIL result. "
                f"Overriding to NEEDS_HUMAN to prevent infinite loop."
            )
            evaluation.result = JudgeResult.NEEDS_HUMAN
            evaluation.feedback = (
                f"[MAX ITERATIONS REACHED] {evaluation.feedback}\n\n"
                f"This document has been regenerated {iteration_count} times "
                f"and still does not meet quality standards. Human review is required."
            )
        
        # Route based on result
        if evaluation.result == JudgeResult.PASS:
            next_stage = pass_stage
            logger.info(f"{trace_name}: PASS → {next_stage.value}")
        elif evaluation.result == JudgeResult.FAIL:
            next_stage = failure_stage
            logger.info(f"{trace_name}: FAIL → {next_stage.value} (regenerate)")
        else:  # NEEDS_HUMAN
            next_stage = human_review_stage
            logger.info(f"{trace_name}: NEEDS_HUMAN → {next_stage.value}")
        
        return {
            evaluation_key: evaluation,
            "current_stage": next_stage,
            "accumulated_cost_usd": (
                state.get("accumulated_cost_usd", 0.0) + response.cost_usd
            ),
        }
    
    except (RuntimeError, KeyError, ValueError, TypeError, Exception) as e:
        logger.error(f"Judge evaluation failed in {trace_name}: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": f"Judge {trace_name} failed: {str(e)}",
            "current_stage": WorkflowStage.FAILED,
        }