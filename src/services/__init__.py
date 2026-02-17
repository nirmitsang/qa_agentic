"""
Services layer for V2 implementation.
Provides document management, locking, and coordination services.
"""

from .document_service import DocumentService
from .lock_service import LockService

__all__ = [
    "DocumentService",
    "LockService",
]