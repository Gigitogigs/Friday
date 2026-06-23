import subprocess
import os
import pathlib
import shutil
import platform
import sys
import glob

from .logger import ActionType, ActionStatus, AuditLogger
from .permission_manager import PermissionManager, PermissionLevel, ActionResult, ActionRequest
from .file_indexer import FileIndexer

class OS_Operator:
    def __init__(self, permission_manager: PermissionManager, logger: AuditLogger, file_indexer: FileIndexer = None):
        self.logger = logger
        self.permission_manager = permission_manager
        self.file_indexer = file_indexer

    def _execute_command(self, permission_level, command, dry_run=False):
        """
        Execute a command with permission checking.
        
        Args:
            permission_level: The permission level required to execute the command
            command: The command to execute
            dry_run: If True, only check permissions without executing
            
        Returns:
            ActionResult indicating if the action is permitted
        """
        # Check if the action is permitted
        action = ActionRequest(
            action_type="execute_command",
            description=f"Execute command: {command}",
            target=command,
            required_level=permission_level
        )
        
        result = self.permission_manager.check_permission(action, dry_run)
        
        if not result.success:
            return result
        
        # Execute the command if not dry_run
        if not dry_run:
            try:
                # Execute the command
                output = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Log the action
                self.logger.log_action(
                    action_type=ActionType.EXECUTE,
                    description=f"Execute command: {command}",
                    permission_level=permission_level.value,
                    status=ActionStatus.SUCCESS,
                    metadata={"output": output.stdout}
                )
                
                return ActionResult(
                    success=True,
                    status="success",
                    message="Command executed successfully",
                    data=output.stdout
                )
            except Exception as e:
                # Log the error
                self.logger.log_action(
                    action_type=ActionType.EXECUTE,
                    description=f"Execute command: {command}",
                    permission_level=permission_level.value,
                    status=ActionStatus.FAILED,
                    metadata={"error": str(e)}
                )
                
                return ActionResult(
                    success=False,
                    status="failed",
                    message=f"Command execution failed: {str(e)}"
                )
        
        return ActionResult(
            success=True,
            status="success",
            message="Command is permitted",
            dry_run=True
        )

    def read_file(self, file_path: str) -> ActionResult:
        """Read the contents of a file after verifying permissions.

        This method resolves the path to an absolute form, checks for 'READ' 
        permissions via the PermissionManager, and logs the action to the audit trail.

        Args:
            file_path: The path to the file to be read. Can be relative or absolute.

        Returns:
            ActionResult: A result object. On success, 'data' contains the file string.
                On failure, 'success' is False and 'message' contains the error.

        Raises:
            UnicodeDecodeError: If the file is not valid UTF-8.
            FileNotFoundError: If the file does not exist (handled via ActionResult).
        """
        # Resolve path to prevent path traversal attacks
        path = pathlib.Path(file_path).resolve()
        
        action = ActionRequest(
            action_type="read_file",
            description=f"Read file content from: {path}",
            target=str(path),
            required_level=PermissionLevel.READ
        )
        
        # Security Gate
        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
            
        try:
            content = path.read_text(encoding="utf-8")
            
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Read file: {path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.SUCCESS,
                metadata={"file_size": path.stat().st_size}
            )
            
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully read {path}",
                data=content
            )
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Failed to read file: {path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error reading file {path}: {str(e)}"
            )
    
    def list_files(self, dir_path: str, recursive:bool=False) -> ActionResult:
        """List files in a directory after verifying permissions.

        This method resolves the path to an absolute form, checks for 'READ' 
        permissions via the PermissionManager, and logs the action to the audit trail.

        Args:
            dir_path: The path to the directory to list. Can be relative or absolute.
            recursive: If True, list files recursively.

        Returns:
            ActionResult: A result object. On success, 'data' contains a list of file paths.
                On failure, 'success' is False and 'message' contains the error.
        """

        path = pathlib.Path(dir_path).resolve()
        
        action = ActionRequest(
            action_type="list_files",
            description=f"List files in directory: {path}",
            target=str(path),
            required_level=PermissionLevel.READ
        )

        if not path.exists():
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Failed to list files: directory does not exist: {path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.FAILED,
                metadata={"error": "Directory does not exist"}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Directory does not exist: {path}"
            )

        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
        
        try:
            if recursive:
                files = [str(file) for file in path.rglob('*') if file.is_file()]
            else:
                files = [str(file) for file in path.iterdir() if file.is_file()]
                
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"List files in directory: {path} (recursive={recursive})",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.SUCCESS,
                metadata={"file_count": len(files)}
            )
            
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully listed files in {path}",
                data=files
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Failed to list files in directory: {path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error listing files in {path}: {str(e)}"
            )

    def move_file(self, source: str, destination: str) -> ActionResult:
        """
        Move a file from source to destination.
        
        Args:
            source: The source path of the file/directory.
            destination: The destination path of the file/directory.

        Returns:
            ActionResult: A result object. On success, "success" is true and "data" contains the destination path. On failure, "success" is false and "message" contains the error.

        """
        # 1. Path Resolution
        source_path = pathlib.Path(source).resolve()
        destination_path = pathlib.Path(destination).resolve()

        # 2. Permission Request Preparation
        action = ActionRequest(
            action_type="move_file",
            description=f"Move {source_path} to {destination_path}",
            target=str(source_path),
            required_level=PermissionLevel.SAFE_WRITE
        )
        
        # 3. Security Gate / Permission Check
        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
        
        # 4. Execution Block
        try:
            if not source_path.exists():
                self.logger.log_action(
                    action_type=ActionType.WRITE,
                    description="File not found",
                    permission_level=PermissionLevel.SAFE_WRITE.value,
                    status=ActionStatus.FAILED,
                    metadata={"source": str(source_path), "destination": str(destination_path)}
                )
                return ActionResult(
                    success=False,
                    status="failed",
                    message=f"File not found: {source_path}"
                )

            if not destination_path.exists():
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                
            shutil.move(str(source_path), str(destination_path))
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Successfully moved {source_path} to {destination_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.SUCCESS,
                metadata={"source": str(source_path), "destination": str(destination_path)}
            )
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully moved {source_path} to {destination_path}",
                data=str(destination_path)
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Error moving file {source_path} to {destination_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error moving file {source_path} to {destination_path}: {str(e)}"
            )

    def copy_file(self, source: str, destination: str) -> ActionResult:
        """
        Copy a file from source to destination.
        
        Args:
            source: The source path of the file/directory.
            destination: The destination path of the file/directory.

        Returns:
            ActionResult: A result object. On success, "success" is true and "data" contains the destination path. On failure, "success" is false and "message" contains the error.

        """
        # 1. Path Resolution
        source_path = pathlib.Path(source).resolve()
        destination_path = pathlib.Path(destination).resolve()

        # 2. Permission Request Preparation
        action = ActionRequest(
            action_type="copy_file",
            description=f"Copy {source_path} to {destination_path}",
            target=str(source_path),
            required_level=PermissionLevel.SAFE_WRITE
        )

        # 3. Security Gate / Permission Check
        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check

        # 4. Execution Block
        try:
            if not source_path.exists():
                self.logger.log_action(
                    action_type=ActionType.WRITE,
                    description="File not found",
                    permission_level=PermissionLevel.SAFE_WRITE.value,
                    status=ActionStatus.FAILED,
                    metadata={"source": str(source_path), "destination": str(destination_path)}
                )
                return ActionResult(
                    success=False,
                    status="failed",
                    message=f"File not found: {source_path}"
                )

            if not destination_path.exists():
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                
            shutil.copy2(str(source_path), str(destination_path))
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Successfully copied {source_path} to {destination_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.SUCCESS,
                metadata={"source": str(source_path), "destination": str(destination_path)}
            )

            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully copied {source_path} to {destination_path}",
                data=str(destination_path)
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Error copying file {source_path} to {destination_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error copying file {source_path} to {destination_path}: {str(e)}"
            )

    def write_file(self, path: str, content: str) -> ActionResult:
        """
        Write content to a file.

        Args:
            path: The path to the file to write to.
            content: The content to write to the file.

        Returns:
            ActionResult: A result object. On success, "success" is true and "data" contains the path to the file. On failure, "success" is false and "message" contains the error.
        """
        target_path = pathlib.Path(path).resolve()
        
        action = ActionRequest(
            action_type="write_file",
            description=f"Write {len(content)} bytes to {target_path.name}",
            target=str(target_path),
            required_level=PermissionLevel.SAFE_WRITE
        )

        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
        
        try:
            # Make sure the folder exists before writing
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Actually write the file
            target_path.write_text(content, encoding="utf-8")
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Successfully wrote to {target_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.SUCCESS,
                metadata={"target": str(target_path), "bytes_written": len(content)}
            )
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully wrote to {target_path}",
                data=str(target_path)
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Error writing to {target_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error writing to {target_path}: {str(e)}"
            )

    def create_directory(self, path: str) -> ActionResult:
        """
        Create a directory.

        Args:
            path: The path to the directory to create.

        Returns:
            ActionResult: A result object. On "success" is true and "data" contains  the path to the created directory. On "success" is false and "message" contains the error.
        """
        target_path = pathlib.Path(path).resolve()

        action = ActionRequest(
            action_type="create_directory",
            description=f"Create a directory at {target_path}",
            target=str(target_path),
            required_level=PermissionLevel.SAFE_WRITE
        )
        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
        
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.mkdir()

            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Created directory {target_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.SUCCESS,
                metadata={"target": str(target_path)}
            )
            return ActionResult(
                success=True,
                status="success",
                message=f"Created directory {target_path}",
                data=str(target_path)
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Error creating directory {target_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error creating directory {target_path}: {str(e)}"
            )

    def append_to_file(self, path: str, content: str) -> ActionResult:
        """
        Append content to a file.

        Args:
            path: The path to the file to append to.
            content: The content to append to the file.

        Returns:
            ActionResult: A result object. On success "success" is true and "data" contains the path to the file. On failure "success" is false and "message" contains the error.
            """

        target_path =pathlib.Path(path).resolve()

        action=ActionRequest(
            action_type="append_to_file",
            description=f"Adds content to the end of a file.",
            target=str(target_path),
            required_level=PermissionLevel.SAFE_WRITE
        )
        permission_check=self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with target_path.open("a", encoding="utf-8") as f:
                f.write("\n" + content)
            
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Appended {len(content)} bytes to {target_path}",
                permission_level=PermissionLevel.SAFE_WRITE.value,
                status=ActionStatus.SUCCESS,
                metadata={"target": str(target_path), "bytes_appended": len(content)}
            )
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully appended {len(content)} bytes to {target_path}",
                data=str(target_path)
            )

        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.WRITE,
                description=f"Error appending to {target_path}",
                status=ActionStatus.FAILED,
                permission_level=PermissionLevel.SAFE_WRITE.value,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error appending to {target_path}: {str(e)}"
            )

    def delete_item(self, path:str) -> ActionResult:
        """
        Deletes an item (file or directory) at the specified path.

        Args:
            path: The path to the item to delete.

        Returns:
            ActionResult: A result object.
        """
        target_path = pathlib.Path(path).resolve()
        
        action = ActionRequest(
            action_type="delete_item",
            description=f"Delete item at {target_path}",
            target=str(target_path),
            required_level=PermissionLevel.SAFE_DELETE
        )
        permission_check=self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
        
        try:
            if not target_path.exists():
                self.logger.log_action(
                    action_type=ActionType.DELETE,
                    description="Attempted to delete non-existent item.",
                    permission_level=PermissionLevel.SAFE_DELETE.value,
                    status=ActionStatus.FAILED,
                    metadata={"target": str(target_path)}
                )
                return ActionResult(
                    success=False,
                    status="failed",
                    message=f"File not found: {target_path}"
                )

            if target_path.is_dir():
                shutil.rmtree(str(target_path))
            else:
                target_path.unlink()

            self.logger.log_action(
                action_type=ActionType.DELETE,
                description=f"Successfully deleted {target_path}",
                permission_level=PermissionLevel.SAFE_DELETE.value,
                status=ActionStatus.SUCCESS,
                metadata={"target": str(target_path)}
            )
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully deleted {target_path}",
                data=str(target_path)
            )
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.DELETE,
                description=f"Error deleting {target_path}",
                permission_level=PermissionLevel.SAFE_DELETE.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error deleting {target_path}: {str(e)}"
            )

    def get_file_metadata(self, path: str) -> ActionResult:
        """
        Get metadata for a file or directory.
        
        Args:
            path: The path to the file or directory.
            
        Returns:
            ActionResult: A result object containing metadata (size, created, modified, etc.) in the data field.
        """
        import datetime
        
        # 1. Path Resolution
        target_path = pathlib.Path(path).resolve()
        
        # 2. Permission Request Preparation
        action = ActionRequest(
            action_type="get_file_metadata",
            description=f"Get metadata for {target_path}",
            target=str(target_path),
            required_level=PermissionLevel.READ
        )
        
        # 3. Security Gate
        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
            
        # 4. Execution Block
        try:
            if not target_path.exists():
                self.logger.log_action(
                    action_type=ActionType.READ,
                    description="Attempted to get metadata for non-existent item.",
                    permission_level=PermissionLevel.READ.value,
                    status=ActionStatus.FAILED,
                    metadata={"target": str(target_path)}
                )
                return ActionResult(
                    success=False,
                    status="failed",
                    message=f"File not found: {target_path}"
                )

            stat_info = target_path.stat()
            file_metadata = {
                "name": target_path.name,
                "is_dir": target_path.is_dir(),
                "is_file": target_path.is_file(),
                "size_bytes": stat_info.st_size,
                "created_at": datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified_at": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            }
            
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Retrieved metadata for {target_path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.SUCCESS,
                metadata={"target": str(target_path)}
            )
            
            return ActionResult(
                success=True,
                status="success",
                message=f"Successfully retrieved metadata for {target_path}",
                data=file_metadata
            )
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Error getting metadata for {target_path}",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error getting metadata for {target_path}: {str(e)}"
            )

    def search_files(self, query: str, max_results: int = 10) -> ActionResult:
        """
        Search for files using the FileIndexer.
        
        Args:
            query: The search query (filename or partial filename).
            max_results: The maximum number of results to return.
            
        Returns:
            ActionResult: A result object containing a list of matching file paths in the data field.
        """
        # Validation
        if not self.file_indexer:
            return ActionResult(
                success=False,
                status="failed",
                message="File indexer is not configured or initialized."
            )

        if not query or not query.strip():
            return ActionResult(
                success=False,
                status="failed",
                message="Search query cannot be empty."
            )

        action = ActionRequest(
            action_type="search_files",
            description=f"Search for files matching '{query}'",
            target=query,
            required_level=PermissionLevel.READ
        )

        permission_check = self.permission_manager.check_permission(action)
        if not permission_check.success:
            return permission_check
            
        try:
            results = self.file_indexer.search_files(query, max_results)
            
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Searched for files matching '{query}'",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.SUCCESS,
                metadata={"query": query, "results_count": len(results)}
            )
            
            return ActionResult(
                success=True,
                status="success",
                message=f"Found {len(results)} matching files.",
                data=results
            )
            
        except Exception as e:
            self.logger.log_action(
                action_type=ActionType.READ,
                description=f"Error searching for files matching '{query}'",
                permission_level=PermissionLevel.READ.value,
                status=ActionStatus.FAILED,
                metadata={"error": str(e)}
            )
            return ActionResult(
                success=False,
                status="failed",
                message=f"Error executing search: {str(e)}"
            )
