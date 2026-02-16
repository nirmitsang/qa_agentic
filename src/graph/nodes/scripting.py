# src/graph/nodes/scripting.py
"""
Test Script Generation Node (Scripting)
Stage 10: Generate test code following approved Code Structure Plan
"""
import logging
from datetime import datetime
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, DocumentVersion
from src.agents.llm_client import call_llm
from src.agents.prompts.scripting_prompt import (
    SCRIPTING_SYSTEM_PROMPT,
    SCRIPTING_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def scripting_node(state: AgentState) -> dict:
    """
    Generate test script following the approved Code Structure Plan.
    The plan is PRIMARY - the agent must follow it strictly.
    
    Returns:
        Partial state dict with script_content, version, history, etc.
    """
    logger.info("Scripting node executing")
    
    try:
        # Read state
        gherkin_content = state.get("gherkin_content", "")
        code_plan_content = state.get("code_plan_content", "")  # PRIMARY input
        team_context = state.get("team_context")
        script_iteration_count = state.get("script_iteration_count", 0)
        judge_evaluation = state.get("judge_code_evaluation")
        current_version = state.get("current_script_version", 0)
        workflow_id = state.get("workflow_id", "")
        
        # Build judge feedback (empty on first attempt)
        judge_feedback = ""
        if judge_evaluation and script_iteration_count > 0:
            judge_feedback = f"Score: {judge_evaluation.score}/100\n{judge_evaluation.feedback}"
        else:
            judge_feedback = "First attempt - no previous feedback."
        
        # Build user prompt - code_plan_content is PRIMARY
        user_prompt = SCRIPTING_USER_PROMPT_TEMPLATE.format(
            gherkin_content=gherkin_content,
            code_plan_content=code_plan_content,  # PRIMARY - must follow strictly
            tech_context_md=team_context.tech_context_md if team_context else "",
            codebase_map_md=team_context.codebase_map_md if team_context else "",
            framework_type=team_context.framework_type.value if team_context else "unknown",
            judge_feedback=judge_feedback,
            iteration=script_iteration_count + 1,
        )
        
        # Call LLM
        response = call_llm(
            system_prompt=SCRIPTING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_name="scripting",
            trace_id=state.get("trace_id"),
        )
        
        # Create DocumentVersion
        new_version = current_version + 1
        doc_version = DocumentVersion(
            document_id=str(uuid4()),
            workflow_id=workflow_id,
            document_type="script",
            version=new_version,
            content=response.content,
            format="python",
            created_by="ai",
            is_approved=False,
            created_at=datetime.utcnow(),
        )
        
        # Update history
        script_history = state.get("script_history", [])
        updated_history = script_history + [doc_version]
        
        logger.info(f"Test Script v{new_version} generated ({len(response.content)} chars)")
        
        return {
            "script_content": response.content,
            "script_filename": "test_generated.py",  # V1: single file
            "current_script_version": new_version,
            "script_history": updated_history,
            "script_iteration_count": script_iteration_count + 1,
            "current_stage": WorkflowStage.JUDGE_CODE,
            "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
        }
    
    except RuntimeError as e:
        logger.error(f"LLM call failed in Scripting: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }