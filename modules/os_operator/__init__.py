"""
OS Operator module for Friday.

Provides safe file, folder, and system operations with permission management.
"""

from .file_ops import FileOperator, FileInfo

__all__ = ['FileOperator', 'FileInfo']
