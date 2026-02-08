# Friday - Core Module
"""
Core infrastructure for the Friday Offline Personal Assistant.
This module provides the foundational components that all other modules depend on.
"""

from .permission_manager import PermissionManager, PermissionLevel
from .logger import AuditLogger, AuditEntry
from .ollama_client import OllamaClient

__all__ = [
    "PermissionManager",
    "PermissionLevel", 
    "AuditLogger",
    "AuditEntry",
    "OllamaClient",
]

__version__ = "0.1.0"
