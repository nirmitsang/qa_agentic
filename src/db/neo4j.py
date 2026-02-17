"""
Neo4j Database - V2 Stub
Provides Neo4j connection management.

This module provides the module-level function required by Task 9.2
and re-exports Neo4jDB from neo4j_client for backward compatibility.
"""

from .neo4j_client import Neo4jDB


def get_neo4j_driver():
    """Get a Neo4j driver instance. # TODO V2"""
    return None


__all__ = ["Neo4jDB", "get_neo4j_driver"]
