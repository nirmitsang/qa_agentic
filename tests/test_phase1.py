# tests/test_phase1.py
import os, pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent

REQUIRED_DIRS = [
    "src/config", "src/graph", "src/graph/nodes", "src/graph/edges",
    "src/agents", "src/agents/prompts", "src/knowledge", "src/knowledge/ingestion",
    "src/knowledge/retrieval", "src/models", "src/services", "src/tools",
    "src/db", "src/utils", "context_files", "tests/unit",
    "tests/integration", "tests/fixtures",
]

REQUIRED_INITS = [
    "src/__init__.py", "src/config/__init__.py", "src/graph/__init__.py",
    "src/graph/nodes/__init__.py", "src/graph/edges/__init__.py",
    "src/agents/__init__.py", "src/agents/prompts/__init__.py",
    "src/knowledge/__init__.py", "src/knowledge/ingestion/__init__.py",
    "src/knowledge/retrieval/__init__.py", "src/models/__init__.py",
    "src/services/__init__.py", "src/tools/__init__.py",
    "src/db/__init__.py", "src/utils/__init__.py",
]

def test_directories_exist():
    for d in REQUIRED_DIRS:
        assert (ROOT / d).is_dir(), f"Missing directory: {d}"

def test_init_files_exist():
    for f in REQUIRED_INITS:
        assert (ROOT / f).is_file(), f"Missing __init__.py: {f}"