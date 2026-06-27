# Friday - Core Module
"""
Core infrastructure for the Friday Offline Personal Assistant.
This module provides the foundational components that all other modules depend on.
"""

from .permission_manager import PermissionManager, PermissionLevel
from .logger import AuditLogger, AuditEntry
from .ollama_client import OllamaClient
from .file_indexer import FileIndexer
from .os_operator import OS_Operator

__all__ = [
    "PermissionManager",
    "PermissionLevel", 
    "AuditLogger",
    "AuditEntry",
    "OllamaClient",
    "FileIndexer",
    "OS_Operator",
]

__version__ = "0.1.0"
