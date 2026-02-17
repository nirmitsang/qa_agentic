# src/graph/nodes/strategy.py
"""
Test Strategy Generation Node
Stage 4: Generate comprehensive test strategy document
"""
import logging
from datetime import datetime, timezone
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, DocumentVersion
from src.agents.llm_client import call_llm
from src.agents.prompts.strategy_prompt import (
    STRATEGY_SYSTEM_PROMPT,
    STRATEGY_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def strategy_node(state: AgentState) -> dict:
    """
    Generate test strategy from approved requirements specification.
    
    Returns:
        Partial state dict with strategy_content, version, history, etc.
    """
    logger.info("Strategy Generation node executing")
    
    try:
        # Read state
        raw_input = state.get("raw_input", "")
        requirements_spec_content = state.get("requirements_spec_content", "")
        team_context = state.get("team_context")
        strategy_iteration_count = state.get("strategy_iteration_count", 0)
        judge_evaluation = state.get("judge_strategy_evaluation")
        current_version = state.get("current_strategy_version", 0)
        workflow_id = state.get("workflow_id", "")
        
        # Build judge feedback (empty on first attempt)
        judge_feedback = ""
        if judge_evaluation and strategy_iteration_count > 0:
            judge_feedback = f"Score: {judge_evaluation.score}/100\n{judge_evaluation.feedback}"
        else:
            judge_feedback = "First attempt - no previous feedback."
        
        # Build user prompt
        user_prompt = STRATEGY_USER_PROMPT_TEMPLATE.format(
            raw_input=raw_input,
            requirements_spec_content=requirements_spec_content,
            tech_context_md=team_context.tech_context_md if team_context else "",
            codebase_map_md=team_context.codebase_map_md if team_context else "",
            framework_type=team_context.framework_type.value if team_context else "unknown",
            human_guidance=state.get("human_guidance") or "None provided.",
            judge_feedback=judge_feedback,
            iteration=strategy_iteration_count + 1,
        )
        
        # Call LLM
        response = call_llm(
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_name="strategy",
            trace_id=state.get("trace_id"),
        )
        
        # Create DocumentVersion
        new_version = current_version + 1
        doc_version = DocumentVersion(
            document_id=str(uuid4()),
            workflow_id=workflow_id,
            document_type="strategy",
            version=new_version,
            content=response.content,
            format="markdown",
            created_by="ai",
            is_approved=False,
            created_at=datetime.now(timezone.utc),
        )
        
        # Update history
        strategy_history = state.get("strategy_history", [])
        updated_history = strategy_history + [doc_version]
        
        logger.info(f"Strategy v{new_version} generated ({len(response.content)} chars)")
        
        return {
            "strategy_content": response.content,
            "current_strategy_version": new_version,
            "strategy_history": updated_history,
            "strategy_iteration_count": strategy_iteration_count + 1,
            "current_stage": WorkflowStage.JUDGE_STRATEGY,
            "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
        }
    
    except (RuntimeError, ValueError, Exception) as e:
        logger.error(f"LLM call failed in Strategy Gen: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }