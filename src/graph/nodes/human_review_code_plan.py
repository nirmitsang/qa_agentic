"""
Human Review Code Plan Node — Gate #4 (Code Structure Plan Approval).
"""

import logging
import re

from src.graph.state import AgentState, WorkflowStage
from src.graph.nodes.human_review_spec import _human_review_base

logger = logging.getLogger(__name__)


def _extract_file_tree(code_plan_content: str) -> str:
    """
    Extract the file tree/structure section from the code plan.

    Looks for markdown code blocks following 'file structure', 'file tree',
    'directory structure', or 'project structure' headings.

    Returns:
        Extracted file tree string, or empty string if not found
    """
    if not code_plan_content:
        return ""

    # Try to find a code block after a file structure heading
    pattern = r"(?:file\s*(?:structure|tree)|directory\s*structure|project\s*structure).*?```(?:\w*\n)?(.*?)```"
    match = re.search(pattern, code_plan_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return ""


def human_review_code_plan_node(state: AgentState) -> dict:
    """
    Gate #4 — Code Structure Plan Approval.

    This gate is MANDATORY — there is no auto-proceed path.

    Pauses graph and waits for human to:
    - APPROVE → Test script generation
    - REJECT → Regenerate code plan
    - EDIT → Store edited plan and proceed to scripting

    Reads:
        - code_plan_content
        - current_code_plan_version
        - judge_code_plan_evaluation

    Returns:
        - approval_gates (updated)
        - current_stage (WorkflowStage)
        - code_plan_content (if edited)
        - human_feedback (if rejected)
    """
    logger.info("Human Review Code Plan node executing (Gate #4)")

    # Extract file tree from code plan for the interrupt payload
    code_plan_content = state.get("code_plan_content", "")
    file_tree = _extract_file_tree(code_plan_content)

    return _human_review_base(
        state=state,
        gate_name="code_plan",
        document_content_key="code_plan_content",
        document_version_key="current_code_plan_version",
        approve_stage=WorkflowStage.SCRIPTING,
        reject_stage=WorkflowStage.CODE_STRUCTURE_PLANNING,
        extra_payload={"file_tree": file_tree} if file_tree else None,
    )