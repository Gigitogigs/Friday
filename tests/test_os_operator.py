"""
    Test for Os Operator module
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.os_operator import OS_Operator
from core.permission_manager import PermissionManager, PermissionLevel, ActionRequest, ActionResult
from core.logger import AuditLogger, ActionType, ActionStatus

#CREATE FIXTURES(KINDA LIKE TEST VARIABLES OF FUNCTIONS IN THE PROGRAM)
@pytest.fixture
def mock_logger():
    """Provides a dummy logger that does bot actually write to disk."""
    return AuditLogger(log_path="dummy_log.jsonl")

@pytest.fixture
def mock_permission_manager():
    """provides a PermissionManager that is configured to allow everything for testing"""
    pm = PermissionManager(config_path="dummy_config.yaml")
    pm.set_approval_callback(lambda desc, preview: True)
    return pm

@pytest.fixture
def os_operator(mock_permission_manager, mock_logger):
    """Provides a ready-to-use OS_Operator instance"""
    return OS_Operator(permission_manager=mock_permission_manager, logger=mock_logger)


#TESTS
class TestCreateFile:
    """Test create file functionality"""

    def test_write_file_success(self, os_operator, tmp_path):
        #1.ARRANGE
        target_file = tmp_path / "test.txt"
        content = "Hello Friday"

        #2.ACT
        result= os_operator.write_file(str(target_file), content)

        #3.ASSERT
        #Verify the Os_Operator returned a successful ActionResult
        assert result.success is True
        assert result.status == "success"
        
        #verify the file was ACTUALLY created on the hard drive
        assert target_file.exists()
        assert target_file.read_text() == content

class TestDeleteItem:
    """Test the OS Destroyer-Lite functionality"""

    def test_delete_item_dry_run(self, os_operator, tmp_path):
        """Verify dry_run returns impacted files without deleting them."""
        #Create a real file in our temporary test folder
        target_file = tmp_path /"do_not_delete.txt"
        target_file.write_text("Important data")

        result = os_operator.delete_item(str(target_file), dry_run=True)

        #Verify the file is in the impacted_files list
        impacted_files = result.data.get("impacted_files", [])
        assert str(target_file) in impacted_files

        assert target_file.exists()

    def test_delete_item_success(self, os_operator, tmp_path):
        target_file = tmp_path /"delete_me.txt"
        target_file.write_text("delete me")

        result = os_operator.delete_item(str(target_file))

        assert result.success is True
        assert result.status == "success"
        assert target_file.exists() is False
        
class TestReadFile:
    """Test Read File Functionality"""
    
    def test_read_file_success(self, os_operator, tmp_path):
        target_file = tmp_path /"sample.txt"
        content="Read me"

        target_file.write_text(content)

        result = os_operator.read_file(str(target_file))

        assert result.success is True
        assert result.status == "success"
        assert result.data == content

class TestListFiles:
    """Test List Files Functionality"""

    def test_list_files_success(self, os_operator, tmp_path):
        file1 = tmp_path / "f1.txt"
        file2 = tmp_path / "f2.txt"
        file1.write_text("Hello")
        file2.write_text("Friday")

        result = os_operator.list_files(str(tmp_path))

        assert result.success is True
        assert result.status == "success"
        assert str(file1) in result.data
        assert str(file2) in result.data

class TestMoveFile:
    """Test Move File Functionality"""

    def test_move_file_success(self, os_operator, tmp_path):
        source = tmp_path /"sample.txt"
        destination = tmp_path/"new_folder"/"sample.txt"

        source.write_text("Move me")
        result = os_operator.move_file(str(source), str(destination))

        assert result.success is True
        assert result.status == "success"
        assert destination.exists()
        assert not source.exists()
    

class TestCopyFile:
    """Test Copy File Functionality"""

    def test_copy_file_success(self, os_operator, tmp_path):
        source = tmp_path / "source.txt"
        destination = tmp_path / "dest" / "source.txt"
        
        source.write_text("Copy me")
        result = os_operator.copy_file(str(source), str(destination))

        assert result.success is True
        assert result.status == "success"
        assert source.exists()
        assert destination.exists()
        assert destination.read_text() == "Copy me"

class TestCreateDirectory:
    """Test Create Directory Functionality"""

    def test_create_directory_success(self, os_operator, tmp_path):
        new_dir = tmp_path / "new_folder"
        
        result = os_operator.create_directory(str(new_dir))

        assert result.success is True
        assert result.status == "success"
        assert new_dir.exists()
        assert new_dir.is_dir()

class TestAppendToFile:
    """Test Append To File Functionality"""

    def test_append_to_file_success(self, os_operator, tmp_path):
        target_file = tmp_path / "append.txt"
        target_file.write_text("First line")
        
        result = os_operator.append_to_file(str(target_file), "Second line")

        assert result.success is True
        assert result.status == "success"
        assert target_file.read_text() == "First line\nSecond line"

class TestGetFileMetadata:
    """Test Get File Metadata Functionality"""

    def test_get_file_metadata_success(self, os_operator, tmp_path):
        target_file = tmp_path / "meta.txt"
        target_file.write_text("metadata test")
        
        result = os_operator.get_file_metadata(str(target_file))

        assert result.success is True
        assert result.status == "success"
        assert "size_bytes" in result.data
        assert "created_at" in result.data
        assert "modified_at" in result.data
        assert result.data["name"] == "meta.txt"

class TestSearchFiles:
    """Test Search Files Functionality"""

    def test_search_files_no_indexer(self, os_operator):
        # Without file_indexer, it should fail gracefully
        result = os_operator.search_files("query")
        
        assert result.success is False
        assert result.status == "failed"
        assert "File indexer is not configured" in result.message
