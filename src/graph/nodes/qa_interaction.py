# src/graph/nodes/qa_interaction.py
"""
QA Interaction Node
Stage 1: Confidence assessment and clarifying question generation
"""
import logging
from datetime import datetime
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, QASession
from src.agents.llm_client import call_llm, extract_json_from_response
from src.agents.prompts.qa_interaction_prompt import (
    QA_INTERACTION_SYSTEM_PROMPT,
    QA_INTERACTION_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def qa_interaction_node(state: AgentState) -> dict:
    """
    Assess confidence and generate clarifying questions if needed.
    
    Returns:
        Partial state dict with qa_sessions, qa_completed, current_stage, etc.
    """
    logger.info("QA Interaction node executing")
    
    try:
        # Read state
        raw_input = state.get("raw_input", "")
        team_context = state.get("team_context")
        qa_sessions = state.get("qa_sessions", [])
        qa_iteration_count = state.get("qa_iteration_count", 0)
        qa_confidence_threshold = state.get("qa_confidence_threshold", 0.85)
        
        # Build previous Q&A summary
        previous_qa_summary = ""
        if qa_sessions:
            previous_qa_summary = "\n\n".join([
                f"Batch {i+1}:\nQuestions: {', '.join([q.text for q in session.questions])}\n"
                f"Answers: {session.answers}"
                for i, session in enumerate(qa_sessions)
            ])
        
        # Build user prompt
        user_prompt = QA_INTERACTION_USER_PROMPT_TEMPLATE.format(
            raw_input=raw_input,
            tech_context_md=team_context.tech_context_md if team_context else "",
            previous_qa_summary=previous_qa_summary if previous_qa_summary else "None",
            batch_number=qa_iteration_count + 1,
            max_batches=3,
            confidence_threshold=qa_confidence_threshold,
        )
        
        # Call LLM
        response = call_llm(
            system_prompt=QA_INTERACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_name="qa_interaction",
            trace_id=state.get("trace_id"),
        )
        
        # Parse JSON response
        result_json = extract_json_from_response(response.content)
        
        # Create QASession (matching the actual dataclass definition)
        new_session = QASession(
            session_id=str(uuid4()),
            batch_number=qa_iteration_count + 1,
            questions=result_json.get("questions", []),
            answers={},  # Will be filled by Streamlit on next iteration
            ai_confidence=result_json.get("ai_confidence", 0.0),
            status="pending_answers",
            created_at=datetime.utcnow(),
        )
        
        # Update qa_sessions list
        updated_sessions = qa_sessions + [new_session]
        
        # Determine if we should proceed or loop back
        can_proceed = result_json.get("can_proceed", False)
        force_proceed = qa_iteration_count >= 2  # Max 3 batches (0, 1, 2)
        
        if can_proceed or force_proceed:
            # Proceed to requirements generation
            logger.info(f"QA confidence sufficient or max iterations reached. Proceeding. (confidence={new_session.ai_confidence})")
            return {
                "qa_sessions": updated_sessions,
                "qa_iteration_count": qa_iteration_count + 1,
                "qa_completed": True,
                "current_stage": WorkflowStage.REQUIREMENTS_SPEC_GEN,
                "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
            }
        else:
            # Loop back for more questions (Streamlit will feed answers)
            logger.info(f"QA confidence low. Generating {len(new_session.questions)} questions.")
            return {
                "qa_sessions": updated_sessions,
                "qa_iteration_count": qa_iteration_count + 1,
                "qa_completed": False,
                "current_stage": WorkflowStage.QA_INTERACTION,
                "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
            }
    
    except RuntimeError as e:
        logger.error(f"LLM call failed in QA Interaction: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }