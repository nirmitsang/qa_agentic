# tests/unit/test_stub_nodes.py
"""
Unit tests for stub nodes - verifies all nodes are importable and callable.
"""

import pytest
import importlib


# All 19 node imports to test
NODE_IMPORTS = [
    ("src.graph.nodes.qa_interaction", "qa_interaction_node"),
    ("src.graph.nodes.requirements_spec_gen", "requirements_spec_gen_node"),
    ("src.graph.nodes.judge_requirements", "judge_requirements_node"),
    ("src.graph.nodes.human_review_spec", "human_review_spec_node"),
    ("src.graph.nodes.strategy", "strategy_node"),
    ("src.graph.nodes.judge_strategy", "judge_strategy_node"),
    ("src.graph.nodes.human_review_strategy", "human_review_strategy_node"),
    ("src.graph.nodes.test_case_generation", "test_case_generation_node"),
    ("src.graph.nodes.judge_test_cases", "judge_test_cases_node"),
    ("src.graph.nodes.human_review_test_cases", "human_review_test_cases_node"),
    ("src.graph.nodes.code_structure_planning", "code_structure_planning_node"),
    ("src.graph.nodes.judge_code_plan", "judge_code_plan_node"),
    ("src.graph.nodes.human_review_code_plan", "human_review_code_plan_node"),
    ("src.graph.nodes.scripting", "scripting_node"),
    ("src.graph.nodes.judge_code", "judge_code_node"),
    ("src.graph.nodes.human_review_code", "human_review_code_node"),
    ("src.graph.nodes.execution", "execution_node"),
    ("src.graph.nodes.healing", "healing_node"),
    ("src.graph.nodes.reporting", "reporting_node"),
]


@pytest.mark.parametrize("module_path,func_name", NODE_IMPORTS)
def test_node_is_importable_and_callable(module_path, func_name):
    """Each node function must be importable and callable."""
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    assert callable(func), f"{func_name} must be callable"