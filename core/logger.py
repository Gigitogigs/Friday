"""
Audit Logger for Friday.

Provides append-only logging of all actions with timestamps, permission levels,
and execution results for security auditing and debugging.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class ActionType(Enum):
    """Types of actions that can be logged."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    SYSTEM = "system"
    PERMISSION = "permission"


class ActionStatus(Enum):
    """Status of an action execution."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"
    FAILED = "failed"
    DRY_RUN = "dry_run"


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    timestamp: str
    action_type: str
    action_description: str
    permission_level: int
    user_approved: Optional[bool]
    status: str
    result: Optional[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        action_type: ActionType,
        action_description: str,
        permission_level: int,
        user_approved: Optional[bool] = None,
        status: ActionStatus = ActionStatus.PENDING,
        result: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "AuditEntry":
        """Factory method to create an audit entry with current timestamp."""
        return cls(
            timestamp=datetime.now().isoformat(),
            action_type=action_type.value,
            action_description=action_description,
            permission_level=permission_level,
            user_approved=user_approved,
            status=status.value,
            result=result,
            metadata=metadata or {}
        )
    
    def to_json(self) -> str:
        """Convert entry to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AuditEntry":
        """Create entry from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class AuditLogger:
    """
    Append-only audit logger for Friday.
    
    All actions are logged to a JSONL file for security auditing.
    The log is append-only to ensure integrity.
    """
    
    def __init__(self, log_path: str = "data/audit_log.jsonl"):
        """
        Initialize the audit logger.
        
        Args:
            log_path: Path to the JSONL log file
        """
        self.log_path = Path(log_path)
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Create the log directory if it doesn't exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.touch()
    
    def log(self, entry: AuditEntry) -> None:
        """
        Append an audit entry to the log.
        
        Args:
            entry: The AuditEntry to log
        """
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")
    
    def log_action(
        self,
        action_type: ActionType,
        description: str,
        permission_level: int,
        user_approved: Optional[bool] = None,
        status: ActionStatus = ActionStatus.PENDING,
        result: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Convenience method to create and log an entry in one call.
        
        Returns the created AuditEntry.
        """
        entry = AuditEntry.create(
            action_type=action_type,
            action_description=description,
            permission_level=permission_level,
            user_approved=user_approved,
            status=status,
            result=result,
            metadata=metadata
        )
        self.log(entry)
        return entry
    
    def get_recent(self, limit: int = 100) -> List[AuditEntry]:
        """
        Get the most recent audit entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of AuditEntry objects, most recent first
        """
        entries = []
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Get last 'limit' entries
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if line:
                try:
                    entries.append(AuditEntry.from_json(line))
                except json.JSONDecodeError:
                    continue
        
        return entries
    
    def get_by_date(self, date: datetime) -> List[AuditEntry]:
        """
        Get all audit entries for a specific date.
        
        Args:
            date: The date to filter by
            
        Returns:
            List of AuditEntry objects for that date
        """
        entries = []
        date_str = date.strftime("%Y-%m-%d")
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and date_str in line:
                    try:
                        entry = AuditEntry.from_json(line)
                        if entry.timestamp.startswith(date_str):
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return entries
    
    def get_by_action_type(self, action_type: ActionType, limit: int = 100) -> List[AuditEntry]:
        """
        Get audit entries filtered by action type.
        
        Args:
            action_type: The ActionType to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of matching AuditEntry objects
        """
        entries = []
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if len(entries) >= limit:
                    break
                    
                line = line.strip()
                if line:
                    try:
                        entry = AuditEntry.from_json(line)
                        if entry.action_type == action_type.value:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return entries
    
    def get_denied_actions(self, limit: int = 50) -> List[AuditEntry]:
        """
        Get actions that were denied by the user.
        
        Useful for reviewing security decisions.
        """
        entries = []
        
        if not self.log_path.exists():
            return entries
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if len(entries) >= limit:
                    break
                    
                line = line.strip()
                if line:
                    try:
                        entry = AuditEntry.from_json(line)
                        if entry.status == ActionStatus.DENIED.value:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return entries
    
    def export(self, format: str = "json") -> str:
        """
        Export the entire audit log.
        
        Args:
            format: Export format ("json" or "csv")
            
        Returns:
            String containing the exported data
        """
        entries = self.get_recent(limit=10000)
        
        if format == "json":
            return json.dumps([asdict(e) for e in entries], indent=2)
        elif format == "csv":
            if not entries:
                return "timestamp,action_type,action_description,permission_level,user_approved,status,result\n"
            
            lines = ["timestamp,action_type,action_description,permission_level,user_approved,status,result"]
            for e in entries:
                lines.append(f'"{e.timestamp}","{e.action_type}","{e.action_description}",{e.permission_level},{e.user_approved},"{e.status}","{e.result or ""}"')
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear(self, confirm: bool = False) -> bool:
        """
        Clear the audit log.
        
        This is a dangerous operation and requires explicit confirmation.
        
        Args:
            confirm: Must be True to actually clear the log
            
        Returns:
            True if cleared, False otherwise
        """
        if not confirm:
            return False
        
        # Create backup before clearing
        if self.log_path.exists():
            backup_path = self.log_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
            self.log_path.rename(backup_path)
            self.log_path.touch()
            return True
        
        return False
