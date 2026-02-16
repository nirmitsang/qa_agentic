# tests/unit/test_context_fetcher.py
"""
Unit tests for context fetcher.
"""

import pytest
from pathlib import Path

from src.knowledge.retrieval.context_fetcher import (
    fetch_context,
    _detect_framework_type,
    _extract_conventions_summary,
)
from src.graph.state import FrameworkType, TeamContext


# Test content samples
PLAYWRIGHT_CONTEXT = "We use Playwright for browser automation and e2e testing."
API_CONTEXT = "Our tests use httpx and pytest to call FastAPI REST endpoints."
UNIT_CONTEXT = "Unit tests use pytest with unittest.mock for mocking."
MIXED_CONTEXT = """
# Tech Context

We use Playwright for E2E tests and pytest for unit tests.
Also using httpx for API calls.
"""


def test_detect_framework_ui_e2e():
    """Detect UI E2E framework from keywords."""
    assert _detect_framework_type(PLAYWRIGHT_CONTEXT) == FrameworkType.UI_E2E


def test_detect_framework_api():
    """Detect API framework from keywords."""
    assert _detect_framework_type(API_CONTEXT) == FrameworkType.API


def test_detect_framework_unit():
    """Detect Unit framework from keywords."""
    assert _detect_framework_type(UNIT_CONTEXT) == FrameworkType.UNIT


def test_detect_framework_unknown():
    """Return UNKNOWN when no keywords match."""
    assert _detect_framework_type("No keywords here.") == FrameworkType.UNKNOWN


def test_detect_framework_case_insensitive():
    """Framework detection is case-insensitive."""
    assert _detect_framework_type("We use PLAYWRIGHT for tests") == FrameworkType.UI_E2E
    assert _detect_framework_type("Using FastAPI endpoints") == FrameworkType.API


def test_extract_conventions_with_section():
    """Extract conventions section when present."""
    content = """
# Tech Context

Some intro text.

## Coding Conventions

- Use snake_case
- Import from src
- Always use type hints

## Other Section

More content here.
"""
    result = _extract_conventions_summary(content)
    assert "Coding Conventions" in result
    assert "snake_case" in result
    assert "Other Section" not in result


def test_extract_conventions_fallback():
    """Fall back to first 500 chars when no conventions section."""
    content = "A" * 1000
    result = _extract_conventions_summary(content)
    assert len(result) == 500
    assert result == "A" * 500


def test_extract_conventions_short_content():
    """Return full content if less than 500 chars and no section."""
    content = "Short content here."
    result = _extract_conventions_summary(content)
    assert result == content


def test_fetch_context_returns_team_context(tmp_path):
    """fetch_context reads files and returns TeamContext."""
    tech = tmp_path / "tech_context.md"
    codebase = tmp_path / "codebase_map.md"
    
    tech.write_text("# Tech Context\nWe use playwright for e2e testing.")
    codebase.write_text("# Codebase Map\n## Existing Utils\n```python\ndef login(): pass\n```")
    
    result = fetch_context(
        team_id="local_team",
        tech_context_path=str(tech),
        codebase_map_path=str(codebase),
    )
    
    assert isinstance(result, TeamContext)
    assert "playwright" in result.tech_context_md.lower()
    assert result.framework_type == FrameworkType.UI_E2E
    assert "Codebase Map" in result.codebase_map_md


def test_fetch_context_graceful_fallback_on_missing_file(tmp_path):
    """fetch_context does NOT raise if a file is missing."""
    tech = tmp_path / "tech_context.md"
    tech.write_text("We use playwright.")
    
    result = fetch_context(
        team_id="local_team",
        tech_context_path=str(tech),
        codebase_map_path="/nonexistent/codebase_map.md",  # Missing file
    )
    
    assert result.codebase_map_md == ""  # Empty string, not an exception
    assert result.tech_context_md != ""  # Tech context loaded successfully


def test_fetch_context_both_files_missing():
    """fetch_context handles both files missing gracefully."""
    result = fetch_context(
        team_id="local_team",
        tech_context_path="/nonexistent/tech.md",
        codebase_map_path="/nonexistent/codebase.md",
    )
    
    assert result.tech_context_md == ""
    assert result.codebase_map_md == ""
    assert result.framework_type == FrameworkType.UNKNOWN
    assert result.conventions_summary == ""


def test_fetch_context_none_paths():
    """fetch_context handles None paths gracefully."""
    result = fetch_context(
        team_id="local_team",
        tech_context_path=None,
        codebase_map_path=None,
    )
    
    assert result.tech_context_md == ""
    assert result.codebase_map_md == ""
    assert result.framework_type == FrameworkType.UNKNOWN


def test_fetch_context_with_component():
    """fetch_context accepts component parameter (unused in V1)."""
    result = fetch_context(
        team_id="local_team",
        component="user_authentication",
        tech_context_path=None,
        codebase_map_path=None,
    )
    
    # Should not raise, component is accepted but unused in V1
    assert isinstance(result, TeamContext)