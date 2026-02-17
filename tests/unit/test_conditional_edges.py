# tests/unit/test_conditional_edges.py
"""
Unit tests for conditional routing functions.
"""

import pytest
from langgraph.graph import END
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
from src.graph.state import WorkflowStage


def test_route_reads_current_stage():
    """Routing function reads current_stage and returns its value."""
    state = {"current_stage": WorkflowStage.REQUIREMENTS_SPEC_GEN}
    result = route_after_qa_interaction(state)
    assert result == "requirements_spec_gen"


def test_route_returns_end_on_missing_stage():
    """Routing function returns END when current_stage is missing."""
    result = route_after_qa_interaction({})
    assert result == END


def test_route_handles_completed():
    """Routing function handles COMPLETED stage."""
    state = {"current_stage": WorkflowStage.COMPLETED}
    result = route_after_human_review_code(state)
    assert result == "completed"


def test_route_handles_failed():
    """Routing function handles FAILED stage by returning END."""
    state = {"current_stage": WorkflowStage.FAILED}
    result = route_after_judge_requirements(state)
    assert result == END


def test_route_after_judge_requirements():
    """route_after_judge_requirements routes correctly."""
    state = {"current_stage": WorkflowStage.HUMAN_REVIEW_SPEC}
    result = route_after_judge_requirements(state)
    assert result == "human_review_spec"


def test_route_after_human_review_spec():
    """route_after_human_review_spec routes to strategy."""
    state = {"current_stage": WorkflowStage.STRATEGY}
    result = route_after_human_review_spec(state)
    assert result == "strategy"


def test_route_after_judge_strategy():
    """route_after_judge_strategy routes correctly."""
    state = {"current_stage": WorkflowStage.HUMAN_REVIEW_STRATEGY}
    result = route_after_judge_strategy(state)
    assert result == "human_review_strategy"


def test_route_after_human_review_strategy():
    """route_after_human_review_strategy routes to test case generation."""
    state = {"current_stage": WorkflowStage.TEST_CASE_GENERATION}
    result = route_after_human_review_strategy(state)
    assert result == "test_case_generation"


def test_route_after_judge_test_cases():
    """route_after_judge_test_cases routes correctly."""
    state = {"current_stage": WorkflowStage.HUMAN_REVIEW_TEST_CASES}
    result = route_after_judge_test_cases(state)
    assert result == "human_review_test_cases"


def test_route_after_human_review_test_cases():
    """route_after_human_review_test_cases routes to code planning."""
    state = {"current_stage": WorkflowStage.CODE_STRUCTURE_PLANNING}
    result = route_after_human_review_test_cases(state)
    assert result == "code_structure_planning"


def test_route_after_judge_code_plan():
    """route_after_judge_code_plan routes correctly."""
    state = {"current_stage": WorkflowStage.HUMAN_REVIEW_CODE_PLAN}
    result = route_after_judge_code_plan(state)
    assert result == "human_review_code_plan"


def test_route_after_human_review_code_plan():
    """route_after_human_review_code_plan routes to scripting."""
    state = {"current_stage": WorkflowStage.SCRIPTING}
    result = route_after_human_review_code_plan(state)
    assert result == "scripting"


def test_route_after_judge_code():
    """route_after_judge_code routes correctly."""
    state = {"current_stage": WorkflowStage.HUMAN_REVIEW_CODE}
    result = route_after_judge_code(state)
    assert result == "human_review_code"


def test_route_handles_string_stage():
    """Routing function handles current_stage as string (not enum)."""
    state = {"current_stage": "requirements_spec_gen"}
    result = route_after_qa_interaction(state)
    assert result == "requirements_spec_gen"


def test_all_routing_functions_exist():
    """Verify all 11 routing functions are defined."""
    routing_functions = [
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
    ]
    
    for func in routing_functions:
        assert callable(func), f"{func.__name__} must be callable"