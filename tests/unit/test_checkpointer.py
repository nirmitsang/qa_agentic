# tests/unit/test_checkpointer.py
"""
Unit tests for checkpointer.
"""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from src.graph.checkpointer import get_checkpointer


def test_get_checkpointer_returns_memory_saver():
    """get_checkpointer returns a MemorySaver instance in V1."""
    checkpointer = get_checkpointer()
    assert isinstance(checkpointer, MemorySaver)


def test_get_checkpointer_is_callable():
    """get_checkpointer function exists and is callable."""
    assert callable(get_checkpointer)


def test_multiple_calls_return_new_instances():
    """Each call to get_checkpointer returns a new MemorySaver instance."""
    cp1 = get_checkpointer()
    cp2 = get_checkpointer()
    
    # Both should be MemorySaver instances
    assert isinstance(cp1, MemorySaver)
    assert isinstance(cp2, MemorySaver)
    
    # They should be different instances
    assert cp1 is not cp2