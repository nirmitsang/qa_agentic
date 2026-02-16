# tests/unit/test_graph_builder.py
"""
Unit tests for graph builder.
"""

import pytest
from src.graph.builder import build_graph


def test_build_graph_returns_compiled_graph():
    """build_graph returns a compiled LangGraph."""
    graph = build_graph()
    
    # Compiled graphs have these attributes
    assert hasattr(graph, "invoke")
    assert hasattr(graph, "stream")
    assert callable(graph.invoke)
    assert callable(graph.stream)


def test_build_graph_is_callable():
    """build_graph function exists and is callable."""
    assert callable(build_graph)


def test_build_graph_can_be_called_multiple_times():
    """Can call build_graph multiple times without errors."""
    graph1 = build_graph()
    graph2 = build_graph()
    
    # Both should be valid compiled graphs
    assert hasattr(graph1, "invoke")
    assert hasattr(graph2, "invoke")
    
    # They should be different instances
    assert graph1 is not graph2