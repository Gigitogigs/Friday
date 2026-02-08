"""
Tests for the Permission Manager module.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.permission_manager import (
    PermissionManager,
    PermissionLevel,
    ActionRequest,
    ActionResult
)
from core.logger import AuditLogger, ActionType, ActionStatus


class TestPermissionLevel:
    """Test PermissionLevel enum."""
    
    def test_permission_levels_ordered(self):
        """Verify permission levels are in correct order."""
        assert PermissionLevel.READ.value < PermissionLevel.SUGGEST.value
        assert PermissionLevel.SUGGEST.value < PermissionLevel.SAFE_WRITE.value
        assert PermissionLevel.SAFE_WRITE.value < PermissionLevel.SYSTEM_WRITE.value
        assert PermissionLevel.SYSTEM_WRITE.value < PermissionLevel.EXECUTE.value
        assert PermissionLevel.EXECUTE.value < PermissionLevel.ADMIN.value


class TestActionRequest:
    """Test ActionRequest dataclass."""
    
    def test_create_action_request(self):
        """Test creating an action request."""
        action = ActionRequest(
            action_type="read_file",
            description="Read file contents",
            target="/path/to/file.txt",
            required_level=PermissionLevel.READ
        )
        
        assert action.action_type == "read_file"
        assert action.target == "/path/to/file.txt"
        assert action.required_level == PermissionLevel.READ
    
    def test_action_matches_pattern(self):
        """Test pattern matching."""
        action = ActionRequest(
            action_type="delete_file",
            description="Delete a file"
        )
        
        assert action.matches_pattern("delete_*")
        assert action.matches_pattern("delete_file")
        assert not action.matches_pattern("read_*")


class TestPermissionManager:
    """Test PermissionManager class."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""friday:
  permissions:
    auto_approve:
      - list_files
      - read_file
    blacklist:
      - format_disk
      - "rm -rf /"
      - dangerous_test
""")
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def temp_log(self):
        """Create a temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def permission_manager(self, temp_config, temp_log):
        """Create a permission manager with temp files."""
        logger = AuditLogger(log_path=temp_log)
        pm = PermissionManager(config_path=temp_config, logger=logger)
        # Set a mock approval callback to avoid CLI stdin issues
        pm.set_approval_callback(lambda desc, preview: False)
        return pm
    
    def test_read_operations_approved(self, permission_manager):
        """Test that read operations are approved without prompts."""
        action = ActionRequest(
            action_type="list_files",
            description="List directory contents",
            required_level=PermissionLevel.READ
        )
        
        result = permission_manager.check_permission(action)
        
        assert result.success
        assert result.status in ["APPROVED", "DRY_RUN"]
    
    def test_blacklisted_operations_denied(self, permission_manager):
        """Test that blacklisted operations are denied."""
        action = ActionRequest(
            action_type="format_disk",
            description="Format the disk",
            required_level=PermissionLevel.ADMIN
        )
        
        result = permission_manager.check_permission(action)
        
        assert not result.success
        assert result.status.upper() == "DENIED"
    
    def test_auto_approved_operations(self, permission_manager):
        """Test that auto-approved operations pass."""
        action = ActionRequest(
            action_type="read_file",
            description="Read a file",
            required_level=PermissionLevel.READ
        )
        
        result = permission_manager.check_permission(action)
        
        assert result.success
    
    def test_add_to_blacklist(self, permission_manager):
        """Test adding patterns to blacklist."""
        permission_manager.add_to_blacklist("dangerous_action")
        
        assert "dangerous_action" in permission_manager.blacklist
    
    def test_add_to_whitelist(self, permission_manager):
        """Test adding patterns to whitelist."""
        permission_manager.add_to_whitelist("safe_action", PermissionLevel.SAFE_WRITE)
        
        assert "safe_action" in permission_manager.whitelist
    
    def test_dry_run_mode(self, permission_manager):
        """Test that dry_run mode works correctly."""
        action = ActionRequest(
            action_type="write_file",
            description="Write to file",
            required_level=PermissionLevel.SAFE_WRITE
        )
        
        result = permission_manager.check_permission(action, dry_run=True)
        
        assert result.dry_run


class TestAuditLogger:
    """Test AuditLogger class."""
    
    @pytest.fixture
    def temp_log(self):
        """Create a temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def logger(self, temp_log):
        """Create a logger with temp file."""
        return AuditLogger(log_path=temp_log)
    
    def test_log_action(self, logger):
        """Test logging an action."""
        entry = logger.log_action(
            action_type=ActionType.READ,
            description="Test action",
            permission_level=0,
            status=ActionStatus.EXECUTED
        )
        
        assert entry.action_description == "Test action"
        assert entry.status == "executed"
    
    def test_get_recent(self, logger):
        """Test getting recent entries."""
        # Log some actions
        for i in range(5):
            logger.log_action(
                action_type=ActionType.READ,
                description=f"Action {i}",
                permission_level=0
            )
        
        entries = logger.get_recent(limit=3)
        
        assert len(entries) == 3
    
    def test_get_denied_actions(self, logger):
        """Test getting denied actions."""
        # Log a denied action
        logger.log_action(
            action_type=ActionType.EXECUTE,
            description="Denied action",
            permission_level=4,
            user_approved=False,
            status=ActionStatus.DENIED
        )
        
        denied = logger.get_denied_actions()
        
        assert len(denied) == 1
        assert denied[0].action_description == "Denied action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
