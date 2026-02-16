# src/knowledge/retrieval/context_fetcher.py
"""
Context fetcher for loading team-specific context.
V1: File-based (reads .md files from disk)
V2: ChromaDB
V3: Pinecone + Neo4j
"""

import logging
from pathlib import Path
from typing import Optional

from src.graph.state import TeamContext, FrameworkType


logger = logging.getLogger(__name__)


# ============================================================================
# FRAMEWORK DETECTION
# ============================================================================

def _detect_framework_type(tech_context_md: str) -> FrameworkType:
    """
    Detect framework type from tech context via keyword scanning.
    
    Keywords from PRD Section 7.3:
    - ui_e2e: playwright, selenium, cypress, browser, e2e
    - api: httpx, requests, fastapi, endpoint, rest, openapi
    - unit: pytest, unittest, mock, patch, fixture
    
    Args:
        tech_context_md: Content of tech_context.md file
        
    Returns:
        FrameworkType enum value
    """
    content_lower = tech_context_md.lower()
    
    # Check UI E2E keywords
    ui_e2e_keywords = ["playwright", "selenium", "cypress", "browser", "e2e"]
    if any(keyword in content_lower for keyword in ui_e2e_keywords):
        return FrameworkType.UI_E2E
    
    # Check API keywords
    api_keywords = ["httpx", "requests", "fastapi", "endpoint", "rest", "openapi"]
    if any(keyword in content_lower for keyword in api_keywords):
        return FrameworkType.API
    
    # Check Unit keywords
    unit_keywords = ["pytest", "unittest", "mock", "patch", "fixture"]
    if any(keyword in content_lower for keyword in unit_keywords):
        return FrameworkType.UNIT
    
    # Default to UNKNOWN if no keywords matched
    return FrameworkType.UNKNOWN


# ============================================================================
# CONVENTIONS EXTRACTION
# ============================================================================

def _extract_conventions_summary(tech_context_md: str) -> str:
    """
    Extract conventions or coding standards section from tech context.
    
    If no conventions section is found, returns the first 500 characters.
    
    Args:
        tech_context_md: Content of tech_context.md file
        
    Returns:
        Conventions summary text
    """
    # Look for common section headers
    lines = tech_context_md.split("\n")
    
    conventions_section = []
    in_conventions = False
    
    for line in lines:
        line_lower = line.lower()
        
        # Check if we're entering a conventions section
        if any(keyword in line_lower for keyword in ["convention", "coding standard", "style guide"]):
            in_conventions = True
            conventions_section.append(line)
            continue
        
        # Check if we're leaving the section (next header)
        if in_conventions and line.startswith("#"):
            break
        
        # Collect lines if we're in the conventions section
        if in_conventions:
            conventions_section.append(line)
    
    # If we found a conventions section, return it
    if conventions_section:
        return "\n".join(conventions_section).strip()
    
    # Otherwise, return first 500 characters
    return tech_context_md[:500] if len(tech_context_md) > 500 else tech_context_md


# ============================================================================
# MAIN FETCH FUNCTION
# ============================================================================

def fetch_context(
    team_id: str,
    component: str = "",
    tech_context_path: Optional[str] = None,
    codebase_map_path: Optional[str] = None,
) -> TeamContext:
    """
    Fetch team-specific context for test generation.
    
    V1 Implementation: Reads local .md files from disk.
    V2 Implementation: Will query ChromaDB.
    V3 Implementation: Will query Pinecone + Neo4j.
    
    Args:
        team_id: Team identifier
        component: Component being tested (unused in V1)
        tech_context_path: Path to tech_context.md file
        codebase_map_path: Path to codebase_map.md file
        
    Returns:
        TeamContext dataclass with loaded content
        
    Note:
        Gracefully handles missing files by returning empty strings with warning logs.
        Does NOT raise exceptions for missing files.
    """
    logger.info(f"Fetching context for team={team_id} component={component}")
    
    # Read tech_context.md
    tech_context_md = ""
    if tech_context_path:
        tech_path = Path(tech_context_path)
        if tech_path.exists():
            try:
                tech_context_md = tech_path.read_text(encoding="utf-8")
                logger.info(f"Loaded tech_context.md ({len(tech_context_md)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read tech_context.md: {e}")
                tech_context_md = ""
        else:
            logger.warning(f"tech_context.md not found at: {tech_context_path}")
            tech_context_md = ""
    
    # Read codebase_map.md
    codebase_map_md = ""
    if codebase_map_path:
        codebase_path = Path(codebase_map_path)
        if codebase_path.exists():
            try:
                codebase_map_md = codebase_path.read_text(encoding="utf-8")
                logger.info(f"Loaded codebase_map.md ({len(codebase_map_md)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read codebase_map.md: {e}")
                codebase_map_md = ""
        else:
            logger.warning(f"codebase_map.md not found at: {codebase_map_path}")
            codebase_map_md = ""
    
    # Detect framework type
    framework_type = _detect_framework_type(tech_context_md) if tech_context_md else FrameworkType.UNKNOWN
    
    # Extract conventions
    conventions_summary = _extract_conventions_summary(tech_context_md) if tech_context_md else ""
    
    logger.info(f"Context loaded: framework={framework_type.value}, conventions_len={len(conventions_summary)}")
    
    return TeamContext(
        tech_context_md=tech_context_md,
        codebase_map_md=codebase_map_md,
        framework_type=framework_type,
        conventions_summary=conventions_summary,
    )