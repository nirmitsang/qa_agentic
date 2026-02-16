# src/utils/gherkin_validator.py
"""
Gherkin syntax validator using gherkin-official 36.0.0.
Used by test case generation node for internal retry loops.
"""

import logging
from dataclasses import dataclass, field

from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from gherkin.token_matcher import TokenMatcher
from gherkin.errors import ParserError


logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION RESULT DATACLASS
# ============================================================================

@dataclass
class GherkinValidationResult:
    """Result of Gherkin syntax validation."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    scenario_count: int = 0
    feature_title: str = ""


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def validate_gherkin(content: str) -> GherkinValidationResult:
    """
    Validate Gherkin syntax using gherkin-official parser.
    
    Uses exact parser API from PRD Section 8.5:
    - Parser() → TokenScanner() → TokenMatcher()
    - On ParserError, returns is_valid=False with error messages
    
    Args:
        content: Gherkin content to validate
        
    Returns:
        GherkinValidationResult with validation status and metadata
    """
    if not content or not content.strip():
        return GherkinValidationResult(
            is_valid=False,
            errors=["Empty or whitespace-only content"],
            scenario_count=0,
            feature_title="",
        )
    
    try:
        # Initialize parser components (PRD Section 8.5 pattern)
        parser = Parser()
        matcher = TokenMatcher()
        scanner = TokenScanner(content)
        
        # Parse the Gherkin document
        doc = parser.parse(scanner, matcher)
        
        # Extract feature metadata
        feature = doc.get("feature")
        if not feature:
            return GherkinValidationResult(
                is_valid=False,
                errors=["No feature found in document"],
                scenario_count=0,
                feature_title="",
            )
        
        feature_title = feature.get("name", "")
        
        # Count scenarios and scenario outlines
        children = feature.get("children", [])
        scenario_count = 0
        
        for child in children:
            # Check for both "scenario" and "scenarioOutline" keys
            if "scenario" in child:
                scenario_count += 1
            elif "scenarioOutline" in child:
                scenario_count += 1
        
        logger.info(
            f"Gherkin validation PASS: feature='{feature_title}' "
            f"scenarios={scenario_count}"
        )
        
        return GherkinValidationResult(
            is_valid=True,
            errors=[],
            scenario_count=scenario_count,
            feature_title=feature_title,
        )
        
    except ParserError as e:
        # Extract error message
        error_msg = str(e)
        
        logger.warning(f"Gherkin validation FAIL: {error_msg}")
        
        return GherkinValidationResult(
            is_valid=False,
            errors=[error_msg],
            scenario_count=0,
            feature_title="",
        )
        
    except Exception as e:
        # Catch any other unexpected errors
        error_msg = f"Unexpected validation error: {str(e)}"
        logger.error(error_msg)
        
        return GherkinValidationResult(
            is_valid=False,
            errors=[error_msg],
            scenario_count=0,
            feature_title="",
        )


# ============================================================================
# ERROR FORMATTING FOR PROMPTS
# ============================================================================

def format_validation_errors_for_prompt(result: GherkinValidationResult) -> str:
    """
    Format validation errors into a prompt-injectable string.
    
    Used by the test case generation node to provide feedback to the LLM
    when Gherkin syntax is invalid.
    
    Args:
        result: GherkinValidationResult with errors
        
    Returns:
        Formatted error string for LLM prompts
    """
    if result.is_valid:
        return ""
    
    if not result.errors:
        return "The Gherkin content has unknown syntax errors."
    
    # Format errors as numbered list
    formatted = "The following Gherkin syntax errors were found:\n"
    
    for i, error in enumerate(result.errors, start=1):
        formatted += f"{i}. {error}\n"
    
    return formatted.strip()