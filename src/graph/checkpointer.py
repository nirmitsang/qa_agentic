# src/graph/checkpointer.py
"""
Checkpointer for LangGraph state persistence.

V1: MemorySaver (in-memory, non-persistent)
V2: PostgresSaver (database-backed persistence)
V3: Enhanced with Redis caching layer
"""

import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer():
    """
    Get the appropriate checkpointer for the current environment.
    
    V1 Implementation: Returns MemorySaver for in-memory state persistence.
    This allows LangGraph to handle interrupts (human review gates) by storing
    state in memory during the session.
    
    V2 Implementation: Will return PostgresSaver for database persistence.
    V3 Implementation: Will add Redis caching layer.
    
    Returns:
        MemorySaver instance for V1
    """
    logger.info("Initializing MemorySaver checkpointer (V1)")
    return MemorySaver()