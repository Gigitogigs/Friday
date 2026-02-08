"""
Permission Manager for Friday.

This is the core security module that gates all system operations.
Every destructive action MUST go through this module for approval.
"""

import fnmatch
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import yaml

from .logger import AuditLogger, AuditEntry, ActionType, ActionStatus


class PermissionLevel(Enum):
    """
    Permission levels for actions.
    
    Higher levels require more trust and typically user approval.
    """
    READ = 0           # Read-only access (safe)
    SUGGEST = 1        # Dry-run operations (preview only)
    SAFE_WRITE = 2     # Low-risk writes (user directories)
    SYSTEM_WRITE = 3   # System modifications (configs, etc.)
    EXECUTE = 4        # Run shell commands
    ADMIN = 5          # Elevated/dangerous operations


@dataclass
class ActionRequest:
    """Represents a request to perform an action."""
    action_type: str
    description: str
    target: Optional[str] = None  # File path, command, etc.
    parameters: Optional[Dict[str, Any]] = None
    required_level: PermissionLevel = PermissionLevel.READ
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if this action matches a glob pattern."""
        return fnmatch.fnmatch(self.action_type, pattern)


@dataclass 
class ActionResult:
    """Result of an action execution."""
    success: bool
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
    dry_run: bool = False


class PermissionManager:
    """
    Central permission manager for Friday.
    
    All potentially destructive operations must be approved through this manager.
    It maintains whitelists, blacklists, and handles user approval workflows.
    """
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        logger: Optional[AuditLogger] = None
    ):
        """
        Initialize the permission manager.
        
        Args:
            config_path: Path to the YAML configuration file
            logger: AuditLogger instance for logging actions
        """
        self.config_path = Path(config_path)
        self.logger = logger or AuditLogger()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize permission lists
        self.whitelist: Dict[str, PermissionLevel] = {}
        self.blacklist: List[str] = []
        self.auto_approve: List[str] = []
        
        self._apply_config()
        
        # User approval callback (can be overridden)
        self._approval_callback: Optional[Callable[[str, str], bool]] = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return self._default_config()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                return config.get("friday", config)
        except Exception:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "permissions": {
                "default_level": "SUGGEST",
                "auto_approve": [
                    "list_files",
                    "read_file",
                    "get_system_info",
                    "get_time",
                ],
                "require_approval": [
                    "delete_*",
                    "execute_*",
                    "write_*",
                    "move_*",
                    "modify_*",
                ],
                "blacklist": [
                    "format_disk",
                    "rm -rf /",
                    "rm -rf /*",
                    "del /f /s /q *",
                    "format c:",
                ]
            }
        }
    
    def _apply_config(self) -> None:
        """Apply configuration to internal state."""
        perms = self.config.get("permissions", {})
        
        # Auto-approve patterns
        self.auto_approve = perms.get("auto_approve", [])
        
        # Blacklist patterns
        self.blacklist = perms.get("blacklist", [])
        
        # Build whitelist from auto_approve
        for pattern in self.auto_approve:
            self.whitelist[pattern] = PermissionLevel.READ
    
    def set_approval_callback(self, callback: Callable[[str, str], bool]) -> None:
        """
        Set the callback function for requesting user approval.
        
        Args:
            callback: Function that takes (action_description, dry_run_preview)
                     and returns True if approved, False otherwise
        """
        self._approval_callback = callback
    
    def check_permission(
        self,
        action: ActionRequest,
        dry_run: bool = False
    ) -> ActionResult:
        """
        Check if an action is permitted.
        
        This method:
        1. Checks if action is blacklisted (immediate deny)
        2. Checks if action is whitelisted/auto-approved
        3. For other actions, requests user approval
        
        Args:
            action: The ActionRequest to check
            dry_run: If True, only check permissions without executing
            
        Returns:
            ActionResult indicating if the action is permitted
        """
        # Log the permission check
        self.logger.log_action(
            action_type=ActionType.PERMISSION,
            description=f"Permission check: {action.description}",
            permission_level=action.required_level.value,
            status=ActionStatus.PENDING,
            metadata={"action_type": action.action_type, "target": action.target}
        )
        
        # Check blacklist first
        if self._is_blacklisted(action):
            self.logger.log_action(
                action_type=ActionType.PERMISSION,
                description=f"BLOCKED: {action.description}",
                permission_level=action.required_level.value,
                user_approved=False,
                status=ActionStatus.DENIED,
                result="Blacklisted action"
            )
            return ActionResult(
                success=False,
                status="DENIED",
                message="This action is blacklisted and cannot be executed.",
                dry_run=dry_run
            )
        
        # Check if auto-approved
        if self._is_auto_approved(action):
            self.logger.log_action(
                action_type=ActionType.PERMISSION,
                description=f"Auto-approved: {action.description}",
                permission_level=action.required_level.value,
                user_approved=True,
                status=ActionStatus.APPROVED,
                result="Auto-approved action"
            )
            return ActionResult(
                success=True,
                status="APPROVED",
                message="Action is auto-approved.",
                dry_run=dry_run
            )
        
        # For READ level, always approve
        if action.required_level == PermissionLevel.READ:
            return ActionResult(
                success=True,
                status="APPROVED",
                message="Read operations are always permitted.",
                dry_run=dry_run
            )
        
        # For SUGGEST level (dry-run), approve but mark as dry-run
        if action.required_level == PermissionLevel.SUGGEST or dry_run:
            return ActionResult(
                success=True,
                status="DRY_RUN",
                message="Dry-run mode - action will be previewed only.",
                dry_run=True
            )
        
        # For higher levels, request approval
        return self._request_approval(action, dry_run)
    
    def _is_blacklisted(self, action: ActionRequest) -> bool:
        """Check if an action matches any blacklist pattern."""
        for pattern in self.blacklist:
            # Check action type
            if action.matches_pattern(pattern):
                return True
            # Check target/command
            if action.target and pattern.lower() in action.target.lower():
                return True
            # Check description
            if pattern.lower() in action.description.lower():
                return True
        return False
    
    def _is_auto_approved(self, action: ActionRequest) -> bool:
        """Check if an action matches any auto-approve pattern."""
        for pattern in self.auto_approve:
            if action.matches_pattern(pattern):
                return True
        return False
    
    def _request_approval(self, action: ActionRequest, dry_run: bool) -> ActionResult:
        """
        Request user approval for an action.
        
        This uses the approval callback if set, otherwise defaults to deny.
        """
        if self._approval_callback is None:
            # No callback set - use CLI prompt
            return self._cli_approval(action, dry_run)
        
        # Generate dry-run preview
        preview = self._generate_preview(action)
        
        # Request approval
        approved = self._approval_callback(action.description, preview)
        
        status = ActionStatus.APPROVED if approved else ActionStatus.DENIED
        self.logger.log_action(
            action_type=ActionType.PERMISSION,
            description=f"User {'approved' if approved else 'denied'}: {action.description}",
            permission_level=action.required_level.value,
            user_approved=approved,
            status=status,
            metadata={"preview": preview}
        )
        
        return ActionResult(
            success=approved,
            status=status.value,
            message="Action approved by user." if approved else "Action denied by user.",
            dry_run=dry_run
        )
    
    def _cli_approval(self, action: ActionRequest, dry_run: bool) -> ActionResult:
        """Request approval via CLI prompt."""
        print("\n" + "=" * 60)
        print("🔒 PERMISSION REQUEST")
        print("=" * 60)
        print(f"\nAction: {action.description}")
        print(f"Type: {action.action_type}")
        print(f"Permission Level: {action.required_level.name}")
        
        if action.target:
            print(f"Target: {action.target}")
        
        preview = self._generate_preview(action)
        if preview:
            print(f"\nPreview:\n{preview}")
        
        print("\n" + "-" * 60)
        
        try:
            response = input("Approve this action? [y/N/never]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        
        if response == "never":
            # Add to blacklist
            self.add_to_blacklist(action.action_type)
            return ActionResult(
                success=False,
                status="BLACKLISTED",
                message="Action added to blacklist.",
                dry_run=dry_run
            )
        
        approved = response in ("y", "yes")
        
        status = ActionStatus.APPROVED if approved else ActionStatus.DENIED
        self.logger.log_action(
            action_type=ActionType.PERMISSION,
            description=f"CLI {'approved' if approved else 'denied'}: {action.description}",
            permission_level=action.required_level.value,
            user_approved=approved,
            status=status
        )
        
        return ActionResult(
            success=approved,
            status=status.value,
            message="Action approved." if approved else "Action denied.",
            dry_run=dry_run
        )
    
    def _generate_preview(self, action: ActionRequest) -> str:
        """Generate a preview of what the action would do."""
        lines = []
        
        if action.action_type.startswith("delete"):
            lines.append(f"⚠️  This will DELETE: {action.target}")
        elif action.action_type.startswith("write"):
            lines.append(f"📝 This will WRITE to: {action.target}")
        elif action.action_type.startswith("execute"):
            lines.append(f"🖥️  This will EXECUTE: {action.target}")
        elif action.action_type.startswith("move"):
            lines.append(f"📦 This will MOVE: {action.target}")
        else:
            lines.append(f"🔧 This will perform: {action.description}")
        
        if action.parameters:
            lines.append("\nParameters:")
            for key, value in action.parameters.items():
                lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines)
    
    def add_to_whitelist(self, pattern: str, level: PermissionLevel) -> None:
        """
        Add an action pattern to the whitelist.
        
        Args:
            pattern: Glob pattern for action types
            level: Maximum permission level to auto-approve
        """
        self.whitelist[pattern] = level
        self.logger.log_action(
            action_type=ActionType.PERMISSION,
            description=f"Added to whitelist: {pattern}",
            permission_level=level.value,
            status=ActionStatus.EXECUTED
        )
    
    def add_to_blacklist(self, pattern: str) -> None:
        """
        Add an action pattern to the blacklist.
        
        Args:
            pattern: Pattern to blacklist
        """
        if pattern not in self.blacklist:
            self.blacklist.append(pattern)
            self.logger.log_action(
                action_type=ActionType.PERMISSION,
                description=f"Added to blacklist: {pattern}",
                permission_level=PermissionLevel.ADMIN.value,
                status=ActionStatus.EXECUTED
            )
    
    def remove_from_blacklist(self, pattern: str) -> bool:
        """
        Remove an action pattern from the blacklist.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if removed, False if not found
        """
        if pattern in self.blacklist:
            self.blacklist.remove(pattern)
            self.logger.log_action(
                action_type=ActionType.PERMISSION,
                description=f"Removed from blacklist: {pattern}",
                permission_level=PermissionLevel.ADMIN.value,
                status=ActionStatus.EXECUTED
            )
            return True
        return False
    
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        """Get recent audit log entries."""
        return self.logger.get_recent(limit=limit)
    
    def save_config(self) -> None:
        """Save current permission configuration to file."""
        config = {
            "friday": {
                "permissions": {
                    "auto_approve": self.auto_approve,
                    "blacklist": self.blacklist,
                }
            }
        }
        
        # Merge with existing config
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or {}
                    if "friday" in existing:
                        existing["friday"]["permissions"] = config["friday"]["permissions"]
                        config = existing
            except Exception:
                pass
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)
