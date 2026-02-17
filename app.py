"""
QA-GPT Streamlit Application — Phase 12

A two-column Streamlit UI for the QA-GPT workflow.
Layout: Sidebar | Progress Bar | [Left: Chat/Q&A/Review] | [Right: Artifact Tabs]
"""

import sys
import os
import tempfile
import logging
from pathlib import Path
from uuid import uuid4

# ============================================================================
# PATH SETUP (PRD Section 8.6 — cross-platform compatibility)
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.config.settings import settings
from src.graph.state import (
    AgentState,
    WorkflowStage,
    WorkflowStatus,
    QASession,
    JudgeResult,
    create_initial_state,
)
from src.knowledge.retrieval.context_fetcher import fetch_context
from src.agents.llm_client import verify_llm_connection
from langgraph.types import Command

logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIG (must be first Streamlit command)
# ============================================================================
st.set_page_config(
    page_title="QA-GPT 🧪",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    /* Progress milestone badges */
    .milestone-done { 
        background: #22c55e; color: white; padding: 4px 10px; 
        border-radius: 12px; font-size: 0.75rem; font-weight: 600;
        text-align: center; 
    }
    .milestone-active { 
        background: #3b82f6; color: white; padding: 4px 10px; 
        border-radius: 12px; font-size: 0.75rem; font-weight: 600;
        text-align: center; animation: pulse 2s infinite;
    }
    .milestone-pending { 
        background: #e5e7eb; color: #6b7280; padding: 4px 10px; 
        border-radius: 12px; font-size: 0.75rem; font-weight: 600;
        text-align: center; 
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    /* Review gate styling */
    .review-gate {
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    /* Compact artifact version info */
    .artifact-meta {
        font-size: 0.8rem;
        color: #6b7280;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# CONSTANTS
# ============================================================================

MILESTONE_LABELS = ["Q&A", "Spec", "Strategy", "Test Cases", "Code Plan", "Script", "Done"]

MILESTONE_MAP = {
    WorkflowStage.QA_INTERACTION: 0,
    WorkflowStage.REQUIREMENTS_SPEC_GEN: 1,
    WorkflowStage.JUDGE_REQUIREMENTS: 1,
    WorkflowStage.HUMAN_REVIEW_SPEC: 1,
    WorkflowStage.STRATEGY: 2,
    WorkflowStage.JUDGE_STRATEGY: 2,
    WorkflowStage.HUMAN_REVIEW_STRATEGY: 2,
    WorkflowStage.TEST_CASE_GENERATION: 3,
    WorkflowStage.JUDGE_TEST_CASES: 3,
    WorkflowStage.HUMAN_REVIEW_TEST_CASES: 3,
    WorkflowStage.CODE_STRUCTURE_PLANNING: 4,
    WorkflowStage.JUDGE_CODE_PLAN: 4,
    WorkflowStage.HUMAN_REVIEW_CODE_PLAN: 4,
    WorkflowStage.SCRIPTING: 5,
    WorkflowStage.JUDGE_CODE: 5,
    WorkflowStage.HUMAN_REVIEW_CODE: 5,
    WorkflowStage.COMPLETED: 6,
}

# Map gate names to their document content/version keys
GATE_CONFIG = {
    "spec": {
        "content_key": "requirements_spec_content",
        "version_key": "current_requirements_spec_version",
        "judge_eval_key": "judge_requirements_evaluation",
        "label": "Requirements Specification",
    },
    "strategy": {
        "content_key": "strategy_content",
        "version_key": "current_strategy_version",
        "judge_eval_key": "judge_strategy_evaluation",
        "label": "Test Strategy",
    },
    "test_cases": {
        "content_key": "gherkin_content",
        "version_key": "current_test_cases_version",
        "judge_eval_key": "judge_test_cases_evaluation",
        "label": "Test Cases (Gherkin)",
    },
    "code_plan": {
        "content_key": "code_plan_content",
        "version_key": "current_code_plan_version",
        "judge_eval_key": "judge_code_plan_evaluation",
        "label": "Code Structure Plan",
    },
    "code": {
        "content_key": "script_content",
        "version_key": "current_script_version",
        "judge_eval_key": "judge_code_evaluation",
        "label": "Test Script",
    },
}

# Map workflow stages to gate names for interrupt detection
HUMAN_REVIEW_STAGES = {
    WorkflowStage.HUMAN_REVIEW_SPEC: "spec",
    WorkflowStage.HUMAN_REVIEW_STRATEGY: "strategy",
    WorkflowStage.HUMAN_REVIEW_TEST_CASES: "test_cases",
    WorkflowStage.HUMAN_REVIEW_CODE_PLAN: "code_plan",
    WorkflowStage.HUMAN_REVIEW_CODE: "code",
}


# ============================================================================
# 12.1 — SESSION STATE INITIALIZATION
# ============================================================================

def _init_session_state():
    """Initialize all session state keys if not already set."""
    defaults = {
        "messages": [],
        "graph_state": None,
        "thread_id": None,
        "workflow_running": False,
        "awaiting_qa": False,
        "awaiting_review": None,
        "bedrock_ok": None,
        "tech_context_path": settings.tech_context_path,
        "codebase_map_path": settings.codebase_map_path,
        "llm_provider": settings.llm_provider,
        "qa_graph": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _get_graph():
    """Get or create the graph instance for this session."""
    if st.session_state.qa_graph is None:
        from src.graph.builder import build_graph
        st.session_state.qa_graph = build_graph()
    return st.session_state.qa_graph


# ============================================================================
# 12.2 — SIDEBAR
# ============================================================================

def _render_sidebar():
    """Render the sidebar with provider info, connection test, uploaders, and session info."""
    st.title("QA-GPT 🧪")
    st.caption("AI-Powered QA Workflow")

    st.divider()

    # Provider display
    provider = st.session_state.llm_provider
    if provider == "bedrock":
        st.info("🔷 Using: **AWS Bedrock**")
    else:
        st.info("🔶 Using: **Google Gemini**")

    # Verify connection button
    if st.button("🔌 Verify Connection", use_container_width=True):
        with st.spinner("Testing connection..."):
            ok = verify_llm_connection()
        if ok:
            st.success("✅ Connection verified!")
            st.session_state.bedrock_ok = True
        else:
            st.error("❌ Connection failed. Check API key in .env")
            st.session_state.bedrock_ok = False

    st.divider()

    # Context file uploaders
    st.subheader("📂 Context Files")

    tech_file = st.file_uploader(
        "Upload tech_context.md",
        type=["md", "txt"],
        key="tech_upload",
    )
    if tech_file:
        # Write to temp file and update path
        tmp_path = os.path.join(tempfile.gettempdir(), "tech_context_uploaded.md")
        Path(tmp_path).write_bytes(tech_file.getvalue())
        st.session_state.tech_context_path = tmp_path
        st.success(f"✅ Loaded ({len(tech_file.getvalue())} bytes)")

    codebase_file = st.file_uploader(
        "Upload codebase_map.md",
        type=["md", "txt"],
        key="codebase_upload",
    )
    if codebase_file:
        tmp_path = os.path.join(tempfile.gettempdir(), "codebase_map_uploaded.md")
        Path(tmp_path).write_bytes(codebase_file.getvalue())
        st.session_state.codebase_map_path = tmp_path
        st.success(f"✅ Loaded ({len(codebase_file.getvalue())} bytes)")

    st.divider()

    # Session info
    st.subheader("📊 Session Info")
    state = st.session_state.graph_state
    if state:
        workflow_id = state.get("workflow_id", "N/A")
        current_stage = state.get("current_stage", "N/A")
        cost = state.get("accumulated_cost_usd", 0.0)
        status = state.get("workflow_status", "N/A")

        st.caption(f"**Workflow:** `{str(workflow_id)[:8]}...`")
        st.caption(f"**Stage:** {current_stage}")
        st.caption(f"**Status:** {status}")
        st.caption(f"**Cost:** ${cost:.4f}")
    else:
        st.caption("No active workflow")

    st.divider()

    # New session button
    if st.button("🔄 New Session", use_container_width=True, type="secondary"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ============================================================================
# 12.3 — PIPELINE PROGRESS BAR
# ============================================================================

def _render_progress_bar(current_stage):
    """Render the pipeline progress bar with 7 milestones."""
    if current_stage is None:
        current_milestone = -1
    elif isinstance(current_stage, WorkflowStage):
        current_milestone = MILESTONE_MAP.get(current_stage, -1)
    else:
        current_milestone = -1

    # Progress value
    progress_value = min((current_milestone + 1) / len(MILESTONE_LABELS), 1.0) if current_milestone >= 0 else 0.0
    st.progress(progress_value)

    # Milestone labels
    cols = st.columns(len(MILESTONE_LABELS))
    for i, (col, label) in enumerate(zip(cols, MILESTONE_LABELS)):
        with col:
            if current_milestone >= 0 and i < current_milestone:
                st.markdown(f'<div class="milestone-done">✓ {label}</div>', unsafe_allow_html=True)
            elif i == current_milestone:
                st.markdown(f'<div class="milestone-active">● {label}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="milestone-pending">{label}</div>', unsafe_allow_html=True)


# ============================================================================
# 12.4 — ARTIFACT TABS (Right Column)
# ============================================================================

def _render_judge_badge(state, judge_eval_key):
    """Render judge evaluation badge if available."""
    judge_eval = state.get(judge_eval_key)
    if judge_eval is None:
        return

    score = judge_eval.score
    result = judge_eval.result

    if isinstance(result, JudgeResult):
        result_value = result.value
    else:
        result_value = str(result)

    if result_value == "PASS":
        st.success(f"✅ Judge: **PASS** (Score: {score}/100)")
    elif result_value == "NEEDS_HUMAN":
        st.warning(f"⚠️ Judge: **NEEDS HUMAN** (Score: {score}/100)")
    elif result_value == "FAIL":
        st.error(f"❌ Judge: **FAIL** (Score: {score}/100)")

    if judge_eval.feedback:
        with st.expander("Judge Feedback"):
            st.markdown(judge_eval.feedback)


def _render_artifact_tabs(state):
    """Render the 5 artifact tabs in the right column."""
    if state is None:
        state = {}

    tabs = st.tabs(["📋 Spec", "🗺️ Strategy", "🧩 Test Cases", "📐 Code Plan", "💻 Script"])

    # Tab 1: Requirements Spec
    with tabs[0]:
        version = state.get("current_requirements_spec_version", 0)
        if version > 0:
            st.caption(f"Version: {version}")
        _render_judge_badge(state, "judge_requirements_evaluation")
        content = state.get("requirements_spec_content", "")
        if content:
            st.markdown(content)
        else:
            st.markdown("*Not generated yet.*")

    # Tab 2: Strategy
    with tabs[1]:
        version = state.get("current_strategy_version", 0)
        if version > 0:
            st.caption(f"Version: {version}")
        _render_judge_badge(state, "judge_strategy_evaluation")
        content = state.get("strategy_content", "")
        if content:
            st.markdown(content)
        else:
            st.markdown("*Not generated yet.*")

    # Tab 3: Test Cases (Gherkin)
    with tabs[2]:
        version = state.get("current_test_cases_version", 0)
        if version > 0:
            st.caption(f"Version: {version}")
        _render_judge_badge(state, "judge_test_cases_evaluation")
        content = state.get("gherkin_content", "")
        if content:
            st.code(content, language="gherkin")
        else:
            st.markdown("*Not generated yet.*")

    # Tab 4: Code Plan
    with tabs[3]:
        version = state.get("current_code_plan_version", 0)
        if version > 0:
            st.caption(f"Version: {version}")
        _render_judge_badge(state, "judge_code_plan_evaluation")
        content = state.get("code_plan_content", "")
        if content:
            st.markdown(content)
        else:
            st.markdown("*Not generated yet.*")

    # Tab 5: Script
    with tabs[4]:
        version = state.get("current_script_version", 0)
        if version > 0:
            st.caption(f"Version: {version}")
        _render_judge_badge(state, "judge_code_evaluation")
        content = state.get("script_content", "")
        if content:
            st.code(content, language="python")
            # Download button
            filename = state.get("script_filename", "test_generated.py")
            st.download_button(
                label="⬇️ Download Test Script",
                data=content,
                file_name=filename,
                mime="text/x-python",
                use_container_width=True,
            )
        else:
            st.markdown("*Not generated yet.*")


# ============================================================================
# 12.5 — Q&A FORM (Left Column)
# ============================================================================

def _render_qa_form():
    """Render the Q&A clarifying questions form."""
    state = st.session_state.graph_state
    if state is None:
        return

    qa_sessions = state.get("qa_sessions", [])
    if not qa_sessions:
        return

    latest_session = qa_sessions[-1]
    confidence = latest_session.ai_confidence if hasattr(latest_session, "ai_confidence") else 0.0
    questions = latest_session.questions if hasattr(latest_session, "questions") else []

    st.subheader("🔍 Clarifying Questions")
    st.caption(f"AI Confidence: {confidence:.0%} (threshold: {settings.qa_confidence_threshold:.0%})")
    st.progress(min(confidence, 1.0))

    if not questions:
        st.info("No questions generated. Pipeline should proceed.")
        return

    with st.form("qa_answers", clear_on_submit=True):
        answers = {}
        for i, q in enumerate(questions):
            # Handle questions as strings or dicts
            if isinstance(q, str):
                q_text = q
                q_id = f"q_{i}"
                required = True
            elif isinstance(q, dict):
                q_text = q.get("text", q.get("id", str(q)))
                q_id = q.get("id", f"q_{i}")
                required = q.get("is_required", True)
            else:
                q_text = getattr(q, "text", str(q))
                q_id = getattr(q, "id", f"q_{i}")
                required = getattr(q, "is_required", True)

            label = f"{'* ' if required else ''}{q_text}"
            answers[q_id] = st.text_area(label, key=f"qa_answer_{i}", height=80)

        submitted = st.form_submit_button("📤 Submit Answers", use_container_width=True, type="primary")

        if submitted:
            # Update the latest session with answers
            latest_session.answers = answers
            latest_session.status = "answered"

            # Update state and resume graph
            graph = _get_graph()
            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            try:
                graph.update_state(config, {
                    "qa_sessions": qa_sessions,
                })
                st.session_state.awaiting_qa = False
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Submitted {len(answers)} answers to clarifying questions.",
                })
                # Resume pipeline
                _resume_pipeline()
            except Exception as e:
                st.error(f"Failed to submit answers: {e}")


# ============================================================================
# 12.6 — HUMAN REVIEW GATE UI (Left Column)
# ============================================================================

def _render_human_review_gate():
    """Render the human review gate UI."""
    gate_name = st.session_state.awaiting_review
    if gate_name is None:
        return

    state = st.session_state.graph_state
    if state is None:
        return

    gate_config = GATE_CONFIG.get(gate_name, {})
    label = gate_config.get("label", gate_name.title())
    content_key = gate_config.get("content_key", "")
    judge_eval_key = gate_config.get("judge_eval_key", "")

    st.subheader(f"👤 Human Review Required: {label}")

    # Show judge info if available
    judge_eval = state.get(judge_eval_key)
    if judge_eval:
        result = judge_eval.result
        if isinstance(result, JudgeResult):
            result_value = result.value
        else:
            result_value = str(result)

        if result_value == "NEEDS_HUMAN":
            st.warning(f"⚠️ The AI judge flagged this for human review. Score: {judge_eval.score}/100")
            if judge_eval.feedback:
                st.markdown(f"**Judge feedback:** {judge_eval.feedback}")
        elif result_value == "PASS":
            st.success(f"✅ Judge passed this artifact. Score: {judge_eval.score}/100")
        elif result_value == "FAIL":
            st.error(f"❌ Judge failed this artifact. Score: {judge_eval.score}/100")
            if judge_eval.feedback:
                st.markdown(f"**Judge feedback:** {judge_eval.feedback}")

    st.info("📖 Review the artifact in the panel on the right, then make your decision below.")

    # Decision form
    with st.form("human_review_form", clear_on_submit=True):
        decision = st.radio(
            "Decision",
            ["APPROVE", "REJECT", "EDIT"],
            horizontal=True,
            index=0,
        )

        feedback = ""
        edited_content = ""

        if decision in ("REJECT", "EDIT"):
            feedback = st.text_area(
                "Feedback / Instructions",
                placeholder="Describe what needs to change...",
                height=100,
            )

        if decision == "EDIT":
            current_content = state.get(content_key, "")
            edited_content = st.text_area(
                "Edit Document",
                value=current_content,
                height=300,
            )

        submitted = st.form_submit_button(
            f"Submit {decision}",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            human_response = {
                "decision": decision,
                "feedback": feedback,
                "edited_content": edited_content,
            }

            try:
                st.session_state.awaiting_review = None
                decision_emoji = {"APPROVE": "✅", "REJECT": "🔄", "EDIT": "✏️"}.get(decision, "")
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"{decision_emoji} {decision} — {label}. {feedback}" if feedback else f"{decision_emoji} {decision} — {label}",
                })

                st.toast(f"{decision_emoji} {label}: {decision}!")

                # Resume pipeline with Command(resume=...) to pass response to interrupt()
                _resume_pipeline(resume_value=human_response)
            except Exception as e:
                st.error(f"Failed to submit review: {e}")


# ============================================================================
# 12.7 — GRAPH STREAMING LOOP
# ============================================================================

def _run_pipeline(user_input: str):
    """Start a new pipeline execution from user input."""
    graph = _get_graph()

    # Fetch context
    team_context = fetch_context(
        team_id=settings.team_id,
        tech_context_path=st.session_state.tech_context_path,
        codebase_map_path=st.session_state.codebase_map_path,
    )

    # Create initial state
    initial_state = create_initial_state(
        raw_input=user_input,
        team_context=team_context,
        team_id=settings.team_id,
        qa_confidence_threshold=settings.qa_confidence_threshold,
    )

    thread_id = initial_state["thread_id"]
    st.session_state.thread_id = thread_id
    st.session_state.workflow_running = True

    config = {"configurable": {"thread_id": thread_id}}

    # Stream the graph
    _stream_graph(graph, initial_state, config)


def _resume_pipeline(resume_value=None):
    """Resume the pipeline after human input (Q&A or review gate)."""
    graph = _get_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if resume_value is not None:
        # Resume from interrupt() — pass Command(resume=...) so the interrupted
        # node receives the human response as the return value of interrupt()
        _stream_graph(graph, Command(resume=resume_value), config)
    else:
        # Resume without interrupt response (e.g., after Q&A answers)
        _stream_graph(graph, None, config)


def _stream_graph(graph, input_state, config):
    """Stream graph execution, handling interrupts and state updates."""
    try:
        with st.spinner("🤖 AI is working..."):
            final_state = None
            for state_snapshot in graph.stream(input_state, config=config, stream_mode="values"):
                final_state = state_snapshot
                st.session_state.graph_state = state_snapshot

            # Check what happened after stream ended
            if final_state is not None:
                current_stage = final_state.get("current_stage")
                workflow_status = final_state.get("workflow_status")

                # Check if we're awaiting Q&A (qa_completed=False, still at QA stage)
                if (current_stage == WorkflowStage.QA_INTERACTION
                        and final_state.get("qa_completed") is False):
                    st.session_state.awaiting_qa = True
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "🔍 I need some clarifying information. Please answer the questions below.",
                    })
                    st.rerun()
                    return

                # Check if we hit a human review gate (interrupt)
                if current_stage in HUMAN_REVIEW_STAGES:
                    gate_name = HUMAN_REVIEW_STAGES[current_stage]
                    st.session_state.awaiting_review = gate_name
                    gate_label = GATE_CONFIG[gate_name]["label"]
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"👤 **Human Review Required:** {gate_label}. Please review the artifact and make your decision.",
                    })
                    st.rerun()
                    return

                # Check for completion
                if current_stage == WorkflowStage.COMPLETED or workflow_status == WorkflowStatus.COMPLETED:
                    st.session_state.workflow_running = False
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "✅ **Pipeline Complete!** Your test script has been generated. Check the Script tab to download it.",
                    })
                    st.toast("🎉 Pipeline complete!")
                    st.rerun()
                    return

                # Check for failure
                if current_stage == WorkflowStage.FAILED or workflow_status == WorkflowStatus.FAILED:
                    error_msg = final_state.get("error_message", "Unknown error")
                    st.session_state.workflow_running = False
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ **Pipeline Failed:** {error_msg}",
                    })
                    st.rerun()
                    return

                # Stream ended normally but not at a known stopping point
                # This might happen with LangGraph interrupts
                # Check graph state for pending interrupts
                try:
                    graph_state = graph.get_state(config)
                    if graph_state and hasattr(graph_state, 'next') and graph_state.next:
                        # There's a next node pending — likely an interrupt
                        next_node = graph_state.next[0] if graph_state.next else None
                        if next_node and next_node.startswith("human_review_"):
                            gate_suffix = next_node.replace("human_review_", "")
                            if gate_suffix in GATE_CONFIG:
                                st.session_state.awaiting_review = gate_suffix
                                gate_label = GATE_CONFIG[gate_suffix]["label"]
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"👤 **Human Review Required:** {gate_label}. Please review the artifact and make your decision.",
                                })
                                st.rerun()
                                return
                except Exception:
                    pass  # If we can't check graph state, continue normally

                st.rerun()

    except Exception as e:
        error_str = str(e)
        error_type = type(e).__name__

        # Handle GraphInterrupt (expected at human review gates)
        if "GraphInterrupt" in error_type or "interrupt" in error_str.lower():
            # Try to detect which gate we're at
            if st.session_state.graph_state:
                current_stage = st.session_state.graph_state.get("current_stage")
                if current_stage in HUMAN_REVIEW_STAGES:
                    gate_name = HUMAN_REVIEW_STAGES[current_stage]
                    st.session_state.awaiting_review = gate_name
                    gate_label = GATE_CONFIG[gate_name]["label"]
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"👤 **Human Review Required:** {gate_label}.",
                    })
                    st.rerun()
                    return

        # Genuine error
        st.session_state.workflow_running = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ **Error:** {error_str}",
        })
        st.error(f"Pipeline error: {error_str}")
        st.rerun()


# ============================================================================
# 12.7 — CHAT INTERFACE
# ============================================================================

def _render_chat_history():
    """Render chat history messages."""
    for msg in st.session_state.messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)


# ============================================================================
# MAIN APP LAYOUT
# ============================================================================

def main():
    """Main application entry point."""
    _init_session_state()

    # --- Sidebar ---
    with st.sidebar:
        _render_sidebar()

    # --- Progress Bar (full width) ---
    state = st.session_state.graph_state
    current_stage = state.get("current_stage") if state else None
    _render_progress_bar(current_stage)

    st.divider()

    # --- Two-column layout ---
    col1, col2 = st.columns([2, 3], gap="large")

    # --- Left Column: Chat / Q&A / Review ---
    with col1:
        # Show the appropriate interface
        if st.session_state.awaiting_qa:
            _render_qa_form()
        elif st.session_state.awaiting_review:
            _render_human_review_gate()
        else:
            # Normal chat interface
            _render_chat_history()

            # Show error state prominently
            if state and state.get("workflow_status") == WorkflowStatus.FAILED:
                st.error(f"❌ Workflow failed: {state.get('error_message', 'Unknown error')}")

            # Chat input
            user_input = st.chat_input(
                "Describe the feature you want to test...",
                disabled=st.session_state.workflow_running,
            )

            if user_input:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "🚀 Starting QA-GPT pipeline...",
                })

                # Run pipeline
                _run_pipeline(user_input)

    # --- Right Column: Artifact Tabs ---
    with col2:
        _render_artifact_tabs(state)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
