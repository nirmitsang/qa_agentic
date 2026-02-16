# src/graph/nodes/requirements_spec_gen.py
"""
Requirements Specification Generation Node
Stage 2: Generate structured requirements document
"""
import logging
from datetime import datetime
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, DocumentVersion
from src.agents.llm_client import call_llm
from src.agents.prompts.requirements_spec_prompt import (
    REQUIREMENTS_SPEC_SYSTEM_PROMPT,
    REQUIREMENTS_SPEC_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def requirements_spec_gen_node(state: AgentState) -> dict:
    """
    Generate requirements specification from raw input and Q&A sessions.
    
    Returns:
        Partial state dict with requirements_spec_content, version, history, etc.
    """
    logger.info("Requirements Spec Generation node executing")
    
    try:
        # Read state
        raw_input = state.get("raw_input", "")
        team_context = state.get("team_context")
        qa_sessions = state.get("qa_sessions", [])
        requirements_iteration_count = state.get("requirements_iteration_count", 0)
        judge_evaluation = state.get("judge_requirements_evaluation")
        current_version = state.get("current_requirements_spec_version", 0)
        workflow_id = state.get("workflow_id", "")
        
        # Build Q&A summary
        qa_summary = ""
        if qa_sessions:
            qa_summary = "\n\n".join([
                f"Batch {session.batch_number}:\n" +
                "\n".join([f"Q: {q.get('text', q) if isinstance(q, dict) else q.text}" for q in session.questions]) +
                f"\nAnswers: {session.answers}"
                for session in qa_sessions
            ])
        else:
            qa_summary = "No Q&A sessions conducted (high initial confidence)."
        
        # Build judge feedback (empty on first attempt)
        judge_feedback = ""
        if judge_evaluation and requirements_iteration_count > 0:
            judge_feedback = f"Score: {judge_evaluation.score}/100\n{judge_evaluation.feedback}"
        else:
            judge_feedback = "First attempt - no previous feedback."
        
        # Build user prompt
        user_prompt = REQUIREMENTS_SPEC_USER_PROMPT_TEMPLATE.format(
            raw_input=raw_input,
            qa_summary=qa_summary,
            tech_context_md=team_context.tech_context_md if team_context else "",
            framework_type=team_context.framework_type.value if team_context else "unknown",
            judge_feedback=judge_feedback,
            iteration=requirements_iteration_count + 1,
        )
        
        # Call LLM
        response = call_llm(
            system_prompt=REQUIREMENTS_SPEC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_name="requirements_spec_gen",
            trace_id=state.get("trace_id"),
        )
        
        # Create DocumentVersion
        new_version = current_version + 1
        doc_version = DocumentVersion(
            document_id=str(uuid4()),
            workflow_id=workflow_id,
            document_type="requirements_spec",
            version=new_version,
            content=response.content,
            format="markdown",
            created_by="ai",
            is_approved=False,
            created_at=datetime.utcnow(),
        )
        
        # Update history
        requirements_history = state.get("requirements_spec_history", [])
        updated_history = requirements_history + [doc_version]
        
        logger.info(f"Requirements spec v{new_version} generated ({len(response.content)} chars)")
        
        return {
            "requirements_spec_content": response.content,
            "current_requirements_spec_version": new_version,
            "requirements_spec_history": updated_history,
            "requirements_iteration_count": requirements_iteration_count + 1,
            "current_stage": WorkflowStage.JUDGE_REQUIREMENTS,
            "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
        }
    
    except RuntimeError as e:
        logger.error(f"LLM call failed in Requirements Spec Gen: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }