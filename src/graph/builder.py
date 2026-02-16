# src/graph/builder.py
"""
LangGraph StateGraph builder - wires all nodes and edges.
"""

import logging
from langgraph.graph import StateGraph, END

from src.graph.state import AgentState, WorkflowStage
from src.graph.checkpointer import get_checkpointer

# Import all 19 nodes
from src.graph.nodes.qa_interaction import qa_interaction_node
from src.graph.nodes.requirements_spec_gen import requirements_spec_gen_node
from src.graph.nodes.judge_requirements import judge_requirements_node
from src.graph.nodes.human_review_spec import human_review_spec_node
from src.graph.nodes.strategy import strategy_node
from src.graph.nodes.judge_strategy import judge_strategy_node
from src.graph.nodes.human_review_strategy import human_review_strategy_node
from src.graph.nodes.test_case_generation import test_case_generation_node
from src.graph.nodes.judge_test_cases import judge_test_cases_node
from src.graph.nodes.human_review_test_cases import human_review_test_cases_node
from src.graph.nodes.code_structure_planning import code_structure_planning_node
from src.graph.nodes.judge_code_plan import judge_code_plan_node
from src.graph.nodes.human_review_code_plan import human_review_code_plan_node
from src.graph.nodes.scripting import scripting_node
from src.graph.nodes.judge_code import judge_code_node
from src.graph.nodes.human_review_code import human_review_code_node
from src.graph.nodes.execution import execution_node
from src.graph.nodes.healing import healing_node
from src.graph.nodes.reporting import reporting_node

# Import all 11 routing functions
from src.graph.edges.conditional import (
    route_after_qa_interaction,
    route_after_judge_requirements,
    route_after_human_review_spec,
    route_after_judge_strategy,
    route_after_human_review_strategy,
    route_after_judge_test_cases,
    route_after_human_review_test_cases,
    route_after_judge_code_plan,
    route_after_human_review_code_plan,
    route_after_judge_code,
    route_after_human_review_code,
)


logger = logging.getLogger(__name__)


def build_graph():
    """
    Build and compile the complete QA-GPT StateGraph.
    
    Graph topology (12 stages, 5 human gates):
    
    START → qa_interaction → requirements_spec_gen → judge_requirements
         → human_review_spec → strategy → judge_strategy
         → human_review_strategy → test_case_generation → judge_test_cases
         → human_review_test_cases → code_structure_planning → judge_code_plan
         → human_review_code_plan → scripting → judge_code
         → human_review_code → END
    
    Judge nodes can loop back to their generator node on FAIL.
    Human review nodes can route to EDIT (back to generator) or APPROVE (forward).
    
    Returns:
        Compiled LangGraph with checkpointer
    """
    logger.info("Building QA-GPT StateGraph...")
    
    # Initialize graph
    graph = StateGraph(AgentState)
    
    # ========================================================================
    # ADD ALL NODES
    # ========================================================================
    
    graph.add_node("qa_interaction", qa_interaction_node)
    graph.add_node("requirements_spec_gen", requirements_spec_gen_node)
    graph.add_node("judge_requirements", judge_requirements_node)
    graph.add_node("human_review_spec", human_review_spec_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("judge_strategy", judge_strategy_node)
    graph.add_node("human_review_strategy", human_review_strategy_node)
    graph.add_node("test_case_generation", test_case_generation_node)
    graph.add_node("judge_test_cases", judge_test_cases_node)
    graph.add_node("human_review_test_cases", human_review_test_cases_node)
    graph.add_node("code_structure_planning", code_structure_planning_node)
    graph.add_node("judge_code_plan", judge_code_plan_node)
    graph.add_node("human_review_code_plan", human_review_code_plan_node)
    graph.add_node("scripting", scripting_node)
    graph.add_node("judge_code", judge_code_node)
    graph.add_node("human_review_code", human_review_code_node)
    graph.add_node("execution", execution_node)
    graph.add_node("healing", healing_node)
    graph.add_node("reporting", reporting_node)
    
    logger.info("Added 19 nodes to graph")
    
    # ========================================================================
    # SET ENTRY POINT
    # ========================================================================
    
    graph.set_entry_point("qa_interaction")
    
    # ========================================================================
    # ADD CONDITIONAL EDGES
    # ========================================================================
    
    # After QA Interaction → Requirements Spec Gen
    graph.add_conditional_edges(
        "qa_interaction",
        route_after_qa_interaction,
        {
            WorkflowStage.REQUIREMENTS_SPEC_GEN.value: "requirements_spec_gen",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Requirements Spec Gen → Judge Requirements
    graph.add_edge("requirements_spec_gen", "judge_requirements")
    
    # After Judge Requirements → Human Review Spec OR back to Requirements (on FAIL)
    graph.add_conditional_edges(
        "judge_requirements",
        route_after_judge_requirements,
        {
            WorkflowStage.HUMAN_REVIEW_SPEC.value: "human_review_spec",
            WorkflowStage.REQUIREMENTS_SPEC_GEN.value: "requirements_spec_gen",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Human Review Spec (Gate #1) → Strategy OR back to Requirements (on EDIT)
    graph.add_conditional_edges(
        "human_review_spec",
        route_after_human_review_spec,
        {
            WorkflowStage.STRATEGY.value: "strategy",
            WorkflowStage.REQUIREMENTS_SPEC_GEN.value: "requirements_spec_gen",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Strategy → Judge Strategy
    graph.add_edge("strategy", "judge_strategy")
    
    # After Judge Strategy → Human Review Strategy OR back to Strategy (on FAIL)
    graph.add_conditional_edges(
        "judge_strategy",
        route_after_judge_strategy,
        {
            WorkflowStage.HUMAN_REVIEW_STRATEGY.value: "human_review_strategy",
            WorkflowStage.STRATEGY.value: "strategy",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Human Review Strategy (Gate #2) → Test Case Gen OR back to Strategy (on EDIT)
    graph.add_conditional_edges(
        "human_review_strategy",
        route_after_human_review_strategy,
        {
            WorkflowStage.TEST_CASE_GENERATION.value: "test_case_generation",
            WorkflowStage.STRATEGY.value: "strategy",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Test Case Generation → Judge Test Cases
    graph.add_edge("test_case_generation", "judge_test_cases")
    
    # After Judge Test Cases → Human Review Test Cases OR back to Test Case Gen (on FAIL)
    graph.add_conditional_edges(
        "judge_test_cases",
        route_after_judge_test_cases,
        {
            WorkflowStage.HUMAN_REVIEW_TEST_CASES.value: "human_review_test_cases",
            WorkflowStage.TEST_CASE_GENERATION.value: "test_case_generation",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Human Review Test Cases (Gate #3) → Code Plan OR back to Test Cases (on EDIT)
    graph.add_conditional_edges(
        "human_review_test_cases",
        route_after_human_review_test_cases,
        {
            WorkflowStage.CODE_STRUCTURE_PLANNING.value: "code_structure_planning",
            WorkflowStage.TEST_CASE_GENERATION.value: "test_case_generation",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Code Structure Planning → Judge Code Plan
    graph.add_edge("code_structure_planning", "judge_code_plan")
    
    # After Judge Code Plan → Human Review Code Plan OR back to Code Plan (on FAIL)
    graph.add_conditional_edges(
        "judge_code_plan",
        route_after_judge_code_plan,
        {
            WorkflowStage.HUMAN_REVIEW_CODE_PLAN.value: "human_review_code_plan",
            WorkflowStage.CODE_STRUCTURE_PLANNING.value: "code_structure_planning",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Human Review Code Plan (Gate #4) → Scripting OR back to Code Plan (on EDIT)
    graph.add_conditional_edges(
        "human_review_code_plan",
        route_after_human_review_code_plan,
        {
            WorkflowStage.SCRIPTING.value: "scripting",
            WorkflowStage.CODE_STRUCTURE_PLANNING.value: "code_structure_planning",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Scripting → Judge Code
    graph.add_edge("scripting", "judge_code")
    
    # After Judge Code → Human Review Code OR back to Scripting (on FAIL)
    graph.add_conditional_edges(
        "judge_code",
        route_after_judge_code,
        {
            WorkflowStage.HUMAN_REVIEW_CODE.value: "human_review_code",
            WorkflowStage.SCRIPTING.value: "scripting",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # After Human Review Code (Gate #5 - FINAL) → COMPLETED OR back to Scripting (on EDIT)
    graph.add_conditional_edges(
        "human_review_code",
        route_after_human_review_code,
        {
            WorkflowStage.COMPLETED.value: END,
            WorkflowStage.SCRIPTING.value: "scripting",
            WorkflowStage.FAILED.value: END,
        },
    )
    
    # ========================================================================
    # V2 EDGES (execution, healing, reporting - not reachable in V1)
    # ========================================================================
    
    # These edges exist for graph completeness but aren't reached in V1
    graph.add_edge("execution", "reporting")
    graph.add_edge("healing", "reporting")
    graph.add_edge("reporting", END)
    
    logger.info("Added all edges to graph")
    
    # ========================================================================
    # COMPILE GRAPH
    # ========================================================================
    
    checkpointer = get_checkpointer()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    logger.info("Graph compiled successfully")
    
    return compiled_graph