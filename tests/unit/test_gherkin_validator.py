# tests/unit/test_gherkin_validator.py
"""
Unit tests for Gherkin validator.
"""

import pytest
from src.utils.gherkin_validator import (
    validate_gherkin,
    format_validation_errors_for_prompt,
    GherkinValidationResult,
)


# ============================================================================
# TEST CONTENT SAMPLES
# ============================================================================

VALID_GHERKIN = """Feature: User Login
  Scenario: Successful login
    Given the user is on the login page
    When they enter valid credentials
    Then they are redirected to the dashboard
"""

INVALID_GHERKIN = """This is not valid Gherkin at all."""

VALID_OUTLINE = """Feature: Data-driven tests
  Scenario Outline: Login with multiple users
    Given I am on the login page
    When I login as <username>
    Then I see the dashboard
    Examples:
      | username |
      | alice    |
      | bob      |
"""

EMPTY_GHERKIN = ""

VALID_MULTIPLE_SCENARIOS = """Feature: User Management
  Scenario: Create user
    Given the admin panel is open
    When I create a new user
    Then the user appears in the list
  
  Scenario: Delete user
    Given a user exists
    When I delete the user
    Then the user is removed from the list
"""


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_validate_valid_gherkin():
    """Valid Gherkin passes validation."""
    result = validate_gherkin(VALID_GHERKIN)
    
    assert result.is_valid is True
    assert result.errors == []
    assert result.scenario_count >= 1
    assert "User Login" in result.feature_title


def test_validate_invalid_gherkin():
    """Invalid Gherkin fails validation."""
    result = validate_gherkin(INVALID_GHERKIN)
    
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_empty_gherkin():
    """Empty content fails validation."""
    result = validate_gherkin(EMPTY_GHERKIN)
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "Empty" in result.errors[0] or "whitespace" in result.errors[0]


def test_validate_whitespace_only():
    """Whitespace-only content fails validation."""
    result = validate_gherkin("   \n  \t  \n   ")
    
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_scenario_outline():
    """Scenario Outline is valid Gherkin."""
    result = validate_gherkin(VALID_OUTLINE)
    
    assert result.is_valid is True
    assert result.scenario_count >= 1
    assert "Data-driven" in result.feature_title


def test_validate_multiple_scenarios():
    """Counts multiple scenarios correctly."""
    result = validate_gherkin(VALID_MULTIPLE_SCENARIOS)
    
    assert result.is_valid is True
    assert result.scenario_count == 2
    assert "User Management" in result.feature_title


def test_validate_gherkin_with_background():
    """Gherkin with Background is valid."""
    content = """Feature: Shopping Cart
  Background:
    Given I am logged in
  
  Scenario: Add item
    When I add an item to cart
    Then the cart count increases
"""
    result = validate_gherkin(content)
    
    assert result.is_valid is True
    assert result.scenario_count >= 1


# ============================================================================
# ERROR FORMATTING TESTS
# ============================================================================

def test_format_errors_for_prompt():
    """Format errors as numbered list for LLM prompts."""
    result = validate_gherkin(INVALID_GHERKIN)
    prompt_text = format_validation_errors_for_prompt(result)
    
    assert "Gherkin syntax errors" in prompt_text
    assert len(prompt_text) > 0


def test_format_errors_empty_for_valid():
    """No error formatting for valid Gherkin."""
    result = validate_gherkin(VALID_GHERKIN)
    prompt_text = format_validation_errors_for_prompt(result)
    
    assert prompt_text == ""


def test_format_errors_numbered_list():
    """Errors are formatted as numbered list."""
    # Create a result with multiple errors
    result = GherkinValidationResult(
        is_valid=False,
        errors=["Error one", "Error two", "Error three"],
        scenario_count=0,
        feature_title="",
    )
    
    prompt_text = format_validation_errors_for_prompt(result)
    
    assert "1. Error one" in prompt_text
    assert "2. Error two" in prompt_text
    assert "3. Error three" in prompt_text


def test_format_errors_no_errors_list():
    """Handle result with is_valid=False but no errors."""
    result = GherkinValidationResult(
        is_valid=False,
        errors=[],
        scenario_count=0,
        feature_title="",
    )
    
    prompt_text = format_validation_errors_for_prompt(result)
    
    assert "unknown" in prompt_text.lower()