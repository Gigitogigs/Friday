"""
File operations module for Friday OS Operator.

Provides safe file and directory operations with permission checks.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core.permission_manager import PermissionManager, PermissionLevel, ActionRequest
from core.logger import AuditLogger, ActionType, ActionStatus


@dataclass
class FileInfo:
    """Information about a file or directory."""
    path: str
    name: str
    size: int
    modified: str
    is_dir: bool
    is_file: bool
    extension: str
    permissions: str


class FileOperator:
    """Operations on files and directories with permission management."""
    
    def __init__(self, permission_manager: PermissionManager, logger: AuditLogger):
        """
        Initialize FileOperator.
        
        Args:
            permission_manager: Permission manager instance
            logger: Audit logger instance
        """
        self.pm = permission_manager
        self.logger = logger
        self.safe_paths = [
            str(Path.home()),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Desktop"),
            str(Path.home() / "Music"),
            str(Path.home() / "Pictures"),
            str(Path.home() / "Videos"),
        ]
    
    def _is_safe_path(self, path: str) -> bool:
        """
        Check if a path is in safe user directories.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            real_path = str(Path(path).resolve())
            for safe_path in self.safe_paths:
                if real_path.startswith(safe_path):
                    return True
            return False
        except Exception:
            return False
    
    def _get_write_level(self, path: str) -> PermissionLevel:
        """
        Determine permission level based on path.
        
        Args:
            path: Path to check
            
        Returns:
            PermissionLevel required for this path
        """
        if self._is_safe_path(path):
            return PermissionLevel.SAFE_WRITE
        return PermissionLevel.SYSTEM_WRITE
    
    def read_file(self, path: str, encoding: str = 'utf-8') -> str:
        """
        Read the contents of a file.
        
        Args:
            path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File contents as string
            
        Raises:
            PermissionError: If permission denied
            FileNotFoundError: If file doesn't exist
        """
        # Create action request
        action = ActionRequest(
            action_type="read_file",
            description=f"Read file: {path}",
            target=path,
            required_level=PermissionLevel.READ
        )
        
        # Check permission
        result = self.pm.check_permission(action)
        if not result.success:
            raise PermissionError(f"Permission denied: {result.message}")
        
        # Execute
        try:
            return Path(path).read_text(encoding=encoding)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except Exception as e:
            raise IOError(f"Error reading file: {e}")
    
    def create_file(self, path: str, content: str, dry_run: bool = True) -> bool:
        """
        Create a new file with content.
        
        Args:
            path: Path where file should be created
            content: Content to write to the file
            dry_run: If True, only preview the action (default: True)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PermissionError: If permission denied
            FileExistsError: If file already exists
        """
        # Determine permission level
        level = self._get_write_level(path)
        
        # Create action request
        action = ActionRequest(
            action_type="create_file",
            description=f"Create file: {path}",
            target=path,
            required_level=level,
            parameters={
                "content_length": len(content),
                "encoding": "utf-8"
            }
        )
        
        # Check permission
        result = self.pm.check_permission(action, dry_run=dry_run)
        if not result.success:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Permission denied: Create {path}",
                permission_level=level.value,
                user_approved=False,
                status=ActionStatus.DENIED
            )
            return False
        
        # Check if file already exists
        if Path(path).exists():
            raise FileExistsError(f"File already exists: {path}")
        
        # Dry-run mode
        if dry_run:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"DRY-RUN: Would create {path}",
                permission_level=level.value,
                status=ActionStatus.DRY_RUN,
                metadata={
                    "content_length": len(content),
                    "path": path
                }
            )
            return True
        
        # Execute
        try:
            Path(path).write_text(content, encoding='utf-8')
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Created file: {path}",
                permission_level=level.value,
                status=ActionStatus.EXECUTED,
                result=f"File created ({len(content)} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Failed to create {path}",
                permission_level=level.value,
                status=ActionStatus.DENIED,
                result=f"Error: {str(e)}"
            )
            raise IOError(f"Error creating file: {e}")
    
    def delete_file(self, path: str, dry_run: bool = True) -> bool:
        """
        Delete a file.
        
        Args:
            path: Path to the file
            dry_run: If True, only preview the action (default: True)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PermissionError: If permission denied
            FileNotFoundError: If file doesn't exist
        """
        # Create action request
        action = ActionRequest(
            action_type="delete_file",
            description=f"Delete file: {path}",
            target=path,
            required_level=PermissionLevel.SYSTEM_WRITE
        )
        
        # Check permission
        result = self.pm.check_permission(action, dry_run=dry_run)
        if not result.success:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Permission denied: Delete {path}",
                permission_level=PermissionLevel.SYSTEM_WRITE.value,
                user_approved=False,
                status=ActionStatus.DENIED
            )
            return False
        
        # Check if file exists
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get file info for logging
        file_size = path_obj.stat().st_size if path_obj.is_file() else 0
        
        # Dry-run mode
        if dry_run:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"DRY-RUN: Would delete {path} ({file_size} bytes)",
                permission_level=PermissionLevel.SYSTEM_WRITE.value,
                status=ActionStatus.DRY_RUN,
                metadata={"file_size": file_size}
            )
            return True
        
        # Execute
        try:
            path_obj.unlink()
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Deleted file: {path}",
                permission_level=PermissionLevel.SYSTEM_WRITE.value,
                status=ActionStatus.EXECUTED,
                result=f"File deleted ({file_size} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Failed to delete {path}",
                permission_level=PermissionLevel.SYSTEM_WRITE.value,
                status=ActionStatus.DENIED,
                result=f"Error: {str(e)}"
            )
            raise IOError(f"Error deleting file: {e}")
    
    
    def list_directory(self, path: str) -> list:
        """
        List contents of a directory.
        
        Args:
            path: Path to the directory
            
        Returns:
            List of FileInfo objects for each item in the directory
            
        Raises:
            PermissionError: If permission denied
            NotADirectoryError: If path is not a directory
        """
        # Create action request
        action = ActionRequest(
            action_type="list_directory",
            description=f"List directory: {path}",
            target=path,
            required_level=PermissionLevel.READ
        )
        
        # Check permission
        result = self.pm.check_permission(action)
        if not result.success:
            raise PermissionError(f"Permission denied: {result.message}")
        
        # Execute
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path_obj.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        
        files = []
        for item in path_obj.iterdir():
            try:
                files.append(self.get_file_info(str(item)))
            except Exception:
                # Skip items we can't read
                continue
        
        return files
    
    def copy_file(self, src: str, dst: str, dry_run: bool = True) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
            dry_run: If True, only preview the action (default: True)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PermissionError: If permission denied
            FileNotFoundError: If source file doesn't exist
        """
        import shutil
        
        # Determine permission level
        level = self._get_write_level(dst)
        
        # Create action request
        action = ActionRequest(
            action_type="copy_file",
            description=f"Copy {src} to {dst}",
            target=dst,
            required_level=level,
            parameters={"source": src}
        )
        
        # Check permission
        result = self.pm.check_permission(action, dry_run=dry_run)
        if not result.success:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Permission denied: Copy {src} to {dst}",
                permission_level=level.value,
                user_approved=False,
                status=ActionStatus.DENIED
            )
            return False
        
        # Check if source exists
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        
        # Check if destination already exists
        dst_path = Path(dst)
        if dst_path.exists():
            raise FileExistsError(f"Destination already exists: {dst}")
        
        # Get file size for logging
        file_size = src_path.stat().st_size
        
        # Dry-run mode
        if dry_run:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"DRY-RUN: Would copy {src} to {dst} ({file_size} bytes)",
                permission_level=level.value,
                status=ActionStatus.DRY_RUN,
                metadata={"source": src, "destination": dst, "size": file_size}
            )
            return True
        
        # Execute
        try:
            shutil.copy2(src, dst)  # copy2 preserves metadata
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Copied {src} to {dst}",
                permission_level=level.value,
                status=ActionStatus.EXECUTED,
                result=f"File copied ({file_size} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Failed to copy {src} to {dst}",
                permission_level=level.value,
                status=ActionStatus.DENIED,
                result=f"Error: {str(e)}"
            )
            raise IOError(f"Error copying file: {e}")
    
    def move_file(self, src: str, dst: str, dry_run: bool = True) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
            dry_run: If True, only preview the action (default: True)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PermissionError: If permission denied
            FileNotFoundError: If source file doesn't exist
        """
        import shutil
        
        # Determine permission level (higher of source and destination)
        src_level = self._get_write_level(src)
        dst_level = self._get_write_level(dst)
        level = max(src_level, dst_level, key=lambda x: x.value)
        
        # Create action request
        action = ActionRequest(
            action_type="move_file",
            description=f"Move {src} to {dst}",
            target=dst,
            required_level=level,
            parameters={"source": src}
        )
        
        # Check permission
        result = self.pm.check_permission(action, dry_run=dry_run)
        if not result.success:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Permission denied: Move {src} to {dst}",
                permission_level=level.value,
                user_approved=False,
                status=ActionStatus.DENIED
            )
            return False
        
        # Check if source exists
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        
        # Check if destination already exists
        dst_path = Path(dst)
        if dst_path.exists():
            raise FileExistsError(f"Destination already exists: {dst}")
        
        # Get file size for logging
        file_size = src_path.stat().st_size
        
        # Dry-run mode
        if dry_run:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"DRY-RUN: Would move {src} to {dst} ({file_size} bytes)",
                permission_level=level.value,
                status=ActionStatus.DRY_RUN,
                metadata={"source": src, "destination": dst, "size": file_size}
            )
            return True
        
        # Execute
        try:
            shutil.move(src, dst)
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Moved {src} to {dst}",
                permission_level=level.value,
                status=ActionStatus.EXECUTED,
                result=f"File moved ({file_size} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Failed to move {src} to {dst}",
                permission_level=level.value,
                status=ActionStatus.DENIED,
                result=f"Error: {str(e)}"
            )
            raise IOError(f"Error moving file: {e}")
    
    def get_file_info(self, path: str) -> FileInfo:
        """
        Get information about a file or directory.
        
        Args:
            path: Path to the file/directory
            
        Returns:
            FileInfo object with file details
            
        Raises:
            FileNotFoundError: If path doesn't exist
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        stat = path_obj.stat()
        
        return FileInfo(
            path=str(path_obj.resolve()),
            name=path_obj.name,
            size=stat.st_size if path_obj.is_file() else 0,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            is_dir=path_obj.is_dir(),
            is_file=path_obj.is_file(),
            extension=path_obj.suffix,
            permissions=oct(stat.st_mode)[-3:]
        )
