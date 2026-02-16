# src/graph/nodes/test_case_generation.py
"""
Test Case Generation Node (Gherkin)
Stage 6: Generate Gherkin feature files from approved strategy
"""
import logging
from datetime import datetime
from uuid import uuid4
from src.graph.state import AgentState, WorkflowStage, WorkflowStatus, DocumentVersion
from src.agents.llm_client import call_llm
from src.utils.gherkin_validator import validate_gherkin, format_validation_errors_for_prompt
from src.agents.prompts.test_case_generation_prompt import (
    TEST_CASE_GENERATION_SYSTEM_PROMPT,
    TEST_CASE_GENERATION_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


def test_case_generation_node(state: AgentState) -> dict:
    """
    Generate Gherkin test cases from approved strategy.
    Includes internal retry loop for Gherkin syntax validation.
    
    Returns:
        Partial state dict with gherkin_content, validation status, version, etc.
    """
    logger.info("Test Case Generation node executing")
    
    try:
        # Read state
        strategy_content = state.get("strategy_content", "")
        requirements_spec_content = state.get("requirements_spec_content", "")
        team_context = state.get("team_context")
        test_cases_iteration_count = state.get("test_cases_iteration_count", 0)
        judge_evaluation = state.get("judge_test_cases_evaluation")
        current_version = state.get("current_gherkin_version", 0)
        workflow_id = state.get("workflow_id", "")
        
        # Build judge feedback (empty on first attempt)
        judge_feedback = ""
        if judge_evaluation and test_case_iteration_count > 0:
            judge_feedback = f"Score: {judge_evaluation.score}/100\n{judge_evaluation.feedback}"
        else:
            judge_feedback = "First attempt - no previous feedback."
        
        # Internal retry loop for Gherkin validation (max 2 attempts)
        max_internal_attempts = 2
        gherkin_content = ""
        validation_result = None
        gherkin_errors = ""
        
        for attempt in range(max_internal_attempts):
            # Build user prompt
            user_prompt = TEST_CASE_GENERATION_USER_PROMPT_TEMPLATE.format(
                strategy_content=strategy_content,
                requirements_spec_content=requirements_spec_content,
                tech_context_md=team_context.tech_context_md if team_context else "",
                framework_type=team_context.framework_type.value if team_context else "unknown",
                judge_feedback=judge_feedback,
                gherkin_errors=gherkin_errors,
                iteration=test_cases_iteration_count + 1,
            )
            
            # Call LLM
            response = call_llm(
                system_prompt=TEST_CASE_GENERATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                trace_name="test_case_generation",
                trace_id=state.get("trace_id"),
            )
            
            gherkin_content = response.content
            
            # Validate Gherkin syntax
            validation_result = validate_gherkin(gherkin_content)
            
            if validation_result.is_valid:
                logger.info(f"Gherkin validation passed on attempt {attempt + 1}")
                break
            else:
                logger.warning(f"Gherkin validation failed on attempt {attempt + 1}: {validation_result.errors}")
                if attempt < max_internal_attempts - 1:
                    # Retry with error feedback
                    gherkin_errors = format_validation_errors_for_prompt(validation_result)
                else:
                    # Max attempts reached, proceed anyway (judge will catch it)
                    logger.error("Gherkin validation failed after max internal retries")
        
        # Create DocumentVersion
        new_version = current_version + 1
        doc_version = DocumentVersion(
            document_id=str(uuid4()),
            workflow_id=workflow_id,
            document_type="gherkin",
            version=new_version,
            content=gherkin_content,
            format="gherkin",
            created_by="ai",
            is_approved=False,
            created_at=datetime.utcnow(),
        )
        
        # Update history
        gherkin_history = state.get("gherkin_history", [])
        updated_history = gherkin_history + [doc_version]
        
        logger.info(f"Gherkin v{new_version} generated ({validation_result.scenario_count} scenarios)")
        
        return {
            "gherkin_content": gherkin_content,
            "gherkin_validation_passed": validation_result.is_valid,
            "current_gherkin_version": new_version,
            "gherkin_history": updated_history,
            "test_cases_iteration_count": test_cases_iteration_count + 1,
            "current_stage": WorkflowStage.JUDGE_TEST_CASES,
            "accumulated_cost_usd": state.get("accumulated_cost_usd", 0.0) + response.cost_usd,
        }
    
    except RuntimeError as e:
        logger.error(f"LLM call failed in Test Case Generation: {e}")
        return {
            "workflow_status": WorkflowStatus.FAILED,
            "error_message": str(e),
            "current_stage": WorkflowStage.FAILED,
        }