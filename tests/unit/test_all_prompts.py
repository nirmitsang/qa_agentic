# tests/unit/test_all_prompts.py
"""
Phase 5 Regression Test: All Agent Prompts
Validates that all 11 prompt files are importable and structurally correct
"""
import pytest

PROMPT_SPECS = [
    ("src.agents.prompts.qa_interaction_prompt", "QA_INTERACTION_SYSTEM_PROMPT", "QA_INTERACTION_USER_PROMPT_TEMPLATE",
     ["{raw_input}", "{tech_context_md}", "{batch_number}"]),
    ("src.agents.prompts.requirements_spec_prompt", "REQUIREMENTS_SPEC_SYSTEM_PROMPT", "REQUIREMENTS_SPEC_USER_PROMPT_TEMPLATE",
     ["{raw_input}", "{judge_feedback}", "{iteration}"]),
    ("src.agents.prompts.judge_requirements_prompt", "JUDGE_REQUIREMENTS_SYSTEM_PROMPT", "JUDGE_REQUIREMENTS_USER_PROMPT_TEMPLATE",
     ["{requirements_spec_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.strategy_prompt", "STRATEGY_SYSTEM_PROMPT", "STRATEGY_USER_PROMPT_TEMPLATE",
     ["{requirements_spec_content}", "{tech_context_md}"]),
    ("src.agents.prompts.judge_strategy_prompt", "JUDGE_STRATEGY_SYSTEM_PROMPT", "JUDGE_STRATEGY_USER_PROMPT_TEMPLATE",
     ["{strategy_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.test_case_generation_prompt", "TEST_CASE_GENERATION_SYSTEM_PROMPT", "TEST_CASE_GENERATION_USER_PROMPT_TEMPLATE",
     ["{strategy_content}", "{gherkin_errors}"]),
    ("src.agents.prompts.judge_test_cases_prompt", "JUDGE_TEST_CASES_SYSTEM_PROMPT", "JUDGE_TEST_CASES_USER_PROMPT_TEMPLATE",
     ["{gherkin_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.code_structure_planner_prompt", "CODE_STRUCTURE_PLANNER_SYSTEM_PROMPT", "CODE_STRUCTURE_PLANNER_USER_PROMPT_TEMPLATE",
     ["{gherkin_content}", "{codebase_map_md}", "{judge_feedback}"]),
    ("src.agents.prompts.judge_code_plan_prompt", "JUDGE_CODE_PLAN_SYSTEM_PROMPT", "JUDGE_CODE_PLAN_USER_PROMPT_TEMPLATE",
     ["{code_plan_content}", "{is_final_iteration}"]),
    ("src.agents.prompts.scripting_prompt", "SCRIPTING_SYSTEM_PROMPT", "SCRIPTING_USER_PROMPT_TEMPLATE",
     ["{code_plan_content}", "{gherkin_content}"]),
    ("src.agents.prompts.judge_code_prompt", "JUDGE_CODE_SYSTEM_PROMPT", "JUDGE_CODE_USER_PROMPT_TEMPLATE",
     ["{script_content}", "{code_plan_content}", "{is_final_iteration}"]),
]

@pytest.mark.parametrize("module_path,sys_name,usr_name,required_vars", PROMPT_SPECS)
def test_prompt_importable_and_has_required_vars(module_path, sys_name, usr_name, required_vars):
    """Every prompt module exports system and user templates with required variables."""
    import importlib
    module = importlib.import_module(module_path)
    system_prompt = getattr(module, sys_name)
    user_template = getattr(module, usr_name)
    assert isinstance(system_prompt, str) and len(system_prompt) > 100, f"{sys_name} too short"
    assert isinstance(user_template, str) and len(user_template) > 50, f"{usr_name} too short"
    for var in required_vars:
        assert var in user_template, f"Missing variable {var} in {usr_name}"

def test_scripting_prompt_contains_strict_instruction():
    """Scripting prompt must contain explicit plan-adherence language."""
    from src.agents.prompts.scripting_prompt import SCRIPTING_SYSTEM_PROMPT
    assert "STRICTLY" in SCRIPTING_SYSTEM_PROMPT or "strictly" in SCRIPTING_SYSTEM_PROMPT.lower()

def test_judge_code_prompt_mentions_plan():
    """Judge code prompt must evaluate plan adherence."""
    from src.agents.prompts.judge_code_prompt import JUDGE_CODE_SYSTEM_PROMPT
    assert "plan" in JUDGE_CODE_SYSTEM_PROMPT.lower()