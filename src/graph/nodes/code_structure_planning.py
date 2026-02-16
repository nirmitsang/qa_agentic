# src/graph/nodes/code_structure_planning.py
"""
Code Structure Planning Node
Stage 8: Create detailed architectural blueprint before code generation
"""
import logging
from datetime import datetime
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, DocumentVersion
from src.agents.llm_client import call_llm
from src.agents.prompts.code_structure_planner_prompt import (
    CODE_STRUCTURE_PLANNER_SYSTEM_PROMPT,
    CODE_STRUCTURE_PLANNER_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def code_structure_planning_node(state: AgentState) -> dict:
    """
    Generate detailed code structure plan before script generation.
    Uses higher token budget (16K) and lower temperature (0.2) for detailed planning.
    
    Returns:
        Partial state dict with code_plan_content, version, history, etc.
    """
    logger.info("Code Structure Planning node executing")
    
    try:
        # Read state
        gherkin_content = state.get("gherkin_content", "")
        team_context = state.get("team_context")
        code_plan_iteration_count = state.get("code_plan_iteration_count", 0)
        judge_evaluation = state.get("judge_code_plan_evaluation")
        current_version = state.get("current_code_plan_version", 0)
        workflow_id = state.get("workflow_id", "")
        
        # Build judge feedback (empty on first attempt)
        judge_feedback = ""
        if judge_evaluation and code_plan_iteration_count > 0:
            judge_feedback = f"Score: {judge_evaluation.score}/100\n{judge_evaluation.feedback}"
        else:
            judge_feedback = "First attempt - no previous feedback."
        
        # Build user prompt
        user_prompt = CODE_STRUCTURE_PLANNER_USER_PROMPT_TEMPLATE.format(
            gherkin_content=gherkin_content,
            tech_context_md=team_context.tech_context_md if team_context else "",
            codebase_map_md=team_context.codebase_map_md if team_context else "",
            conventions_summary=team_context.conventions_summary if team_context else "",
            framework_type=team_context.framework_type.value if team_context else "unknown",
            judge_feedback=judge_feedback,
            iteration=code_plan_iteration_count + 1,
        )
        
        # Call LLM with higher token budget and lower temperature for detailed planning
        response = call_llm(
            system_prompt=CODE_STRUCTURE_PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_name="code_structure_planning",
            trace_id=state.get("trace_id"),
            temperature=0.2,  # Lower temperature for more deterministic planning
            max_tokens=16384,  # Higher token budget for detailed output
        )
        
        # Create DocumentVersion
        new_version = current_version + 1
        doc_version = DocumentVersion(
            document_id=str(uuid4()),
            workflow_id=workflow_id,
            document_type="code_plan",
            version=new_version,
            content=response.content,
            format="markdown",
            created_by="ai",
            is_approved=False,
            created_at=datetime.utcnow(),
        )
        
        # Update history
        code_plan_history = state.get("code_plan_history", [])
        updated_history = code_plan_history + [doc_version]
        
        logger.info(f"Code Structure Plan v{new_version} generated ({len(response.content)} chars)")
        
        return {
            "code_plan_content": response.content,
            "current_code_plan_version": new_version,
            "code_plan_history": updated_history,
            "code_plan_iteration_count": code_plan_iteration_count + 1,
            "current_stage": WorkflowStage.JUDGE_CODE_PLAN,
            "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
        }
    
    except RuntimeError as e:
        logger.error(f"LLM call failed in Code Structure Planning: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }