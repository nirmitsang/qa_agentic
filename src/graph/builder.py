"""
Graph Builder - Assembles the QA-GPT workflow graph.

This module constructs the complete LangGraph workflow by:
1. Importing all real node implementations
2. Defining the graph topology
3. Adding conditional routing edges
4. Compiling the final graph
"""

from langgraph.graph import StateGraph, END
from src.graph.checkpointer import get_checkpointer
from src.graph.state import AgentState
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

# ==========================================
# REAL NODE IMPORTS - Phases 6, 7, 8
# ==========================================

# Phase 6: Generative Nodes
from src.graph.nodes.qa_interaction import qa_interaction_node
from src.graph.nodes.requirements_spec_gen import requirements_spec_gen_node
from src.graph.nodes.strategy import strategy_node
from src.graph.nodes.test_case_generation import test_case_generation_node
from src.graph.nodes.code_structure_planning import code_structure_planning_node
from src.graph.nodes.scripting import scripting_node

# Phase 7: Judge Nodes
from src.graph.nodes.judge_requirements import judge_requirements_node
from src.graph.nodes.judge_strategy import judge_strategy_node
from src.graph.nodes.judge_test_cases import judge_test_cases_node
from src.graph.nodes.judge_code_plan import judge_code_plan_node
from src.graph.nodes.judge_code import judge_code_node

# Phase 8: Human Review Nodes
from src.graph.nodes.human_review_spec import human_review_spec_node
from src.graph.nodes.human_review_strategy import human_review_strategy_node
from src.graph.nodes.human_review_test_cases import human_review_test_cases_node
from src.graph.nodes.human_review_code_plan import human_review_code_plan_node
from src.graph.nodes.human_review_code import human_review_code_node

# Phase 9: V2 Node Stubs (for future use)
from src.graph.nodes.execution import execution_node
from src.graph.nodes.healing import healing_node
from src.graph.nodes.reporting import reporting_node


def build_graph() -> StateGraph:
    """
    Build the complete QA-GPT workflow graph.
    
    Graph Flow:
    1. QA Interaction (gather requirements)
    2. Requirements Spec Generation
    3. Judge Requirements → [PASS/FAIL/NEEDS_HUMAN]
    4. Human Review Spec (if needed)
    5. Strategy Planning
    6. Judge Strategy → [PASS/FAIL/NEEDS_HUMAN]
    7. Human Review Strategy (if needed)
    8. Test Case Generation
    9. Judge Test Cases → [PASS/FAIL/NEEDS_HUMAN]
    10. Human Review Test Cases (if needed)
    11. Code Structure Planning
    12. Judge Code Plan → [PASS/FAIL/NEEDS_HUMAN]
    13. Human Review Code Plan (if needed)
    14. Scripting (final code generation)
    15. Judge Code → [PASS/FAIL/NEEDS_HUMAN]
    16. Human Review Code (if needed)
    17. END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize graph
    workflow = StateGraph(AgentState)
    
    # ==========================================
    # ADD NODES
    # ==========================================
    
    # Entry point
    workflow.add_node("qa_interaction", qa_interaction_node)
    
    # Requirements flow
    workflow.add_node("requirements_spec_gen", requirements_spec_gen_node)
    workflow.add_node("judge_requirements", judge_requirements_node)
    workflow.add_node("human_review_spec", human_review_spec_node)
    
    # Strategy flow
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("judge_strategy", judge_strategy_node)
    workflow.add_node("human_review_strategy", human_review_strategy_node)
    
    # Test cases flow
    workflow.add_node("test_case_generation", test_case_generation_node)
    workflow.add_node("judge_test_cases", judge_test_cases_node)
    workflow.add_node("human_review_test_cases", human_review_test_cases_node)
    
    # Code plan flow
    workflow.add_node("code_structure_planning", code_structure_planning_node)
    workflow.add_node("judge_code_plan", judge_code_plan_node)
    workflow.add_node("human_review_code_plan", human_review_code_plan_node)
    
    # Final code flow
    workflow.add_node("scripting", scripting_node)
    workflow.add_node("judge_code", judge_code_node)
    workflow.add_node("human_review_code", human_review_code_node)
    
    # V2 nodes (not yet wired)
    # workflow.add_node("execution", execution_node)
    # workflow.add_node("healing", healing_node)
    # workflow.add_node("reporting", reporting_node)
    
    # ==========================================
    # SET ENTRY POINT
    # ==========================================
    
    workflow.set_entry_point("qa_interaction")
    
    # ==========================================
    # ADD CONDITIONAL EDGES
    # ==========================================
    # Note: The routing functions return the WorkflowStage.value (string)
    # which corresponds to the next node name. The nodes themselves
    # update state["current_stage"] to determine routing.
    
    # After QA Interaction → Requirements Spec Gen
    workflow.add_conditional_edges(
        "qa_interaction",
        route_after_qa_interaction,
    )
    
    # After Requirements Spec Gen → Judge Requirements
    # (No routing needed - always goes to judge)
    workflow.add_edge("requirements_spec_gen", "judge_requirements")
    
    # After Judge Requirements → Route based on result
    workflow.add_conditional_edges(
        "judge_requirements",
        route_after_judge_requirements,
    )
    
    # After Human Review Spec → Route based on action
    workflow.add_conditional_edges(
        "human_review_spec",
        route_after_human_review_spec,
    )
    
    # After Strategy → Judge Strategy
    workflow.add_edge("strategy", "judge_strategy")
    
    # After Judge Strategy → Route based on result
    workflow.add_conditional_edges(
        "judge_strategy",
        route_after_judge_strategy,
    )
    
    # After Human Review Strategy → Route based on action
    workflow.add_conditional_edges(
        "human_review_strategy",
        route_after_human_review_strategy,
    )
    
    # After Test Case Generation → Judge Test Cases
    workflow.add_edge("test_case_generation", "judge_test_cases")
    
    # After Judge Test Cases → Route based on result
    workflow.add_conditional_edges(
        "judge_test_cases",
        route_after_judge_test_cases,
    )
    
    # After Human Review Test Cases → Route based on action
    workflow.add_conditional_edges(
        "human_review_test_cases",
        route_after_human_review_test_cases,
    )
    
    # After Code Structure Planning → Judge Code Plan
    workflow.add_edge("code_structure_planning", "judge_code_plan")
    
    # After Judge Code Plan → Route based on result
    workflow.add_conditional_edges(
        "judge_code_plan",
        route_after_judge_code_plan,
    )
    
    # After Human Review Code Plan → Route based on action
    workflow.add_conditional_edges(
        "human_review_code_plan",
        route_after_human_review_code_plan,
    )
    
    # After Scripting → Judge Code
    workflow.add_edge("scripting", "judge_code")
    
    # After Judge Code → Route based on result (final judge)
    workflow.add_conditional_edges(
        "judge_code",
        route_after_judge_code,
    )
    
    # After Human Review Code → Route based on action (final gate)
    workflow.add_conditional_edges(
        "human_review_code",
        route_after_human_review_code,
    )
    
    # ==========================================
    # COMPILE GRAPH
    # ==========================================
    
    return workflow.compile(checkpointer=get_checkpointer())


# ==========================================
# GRAPH INSTANCE (Singleton)
# ==========================================

# Create the compiled graph instance
qa_graph = build_graph()