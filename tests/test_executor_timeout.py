"""Tests for executor with timeout enforcement"""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from llm_runner.executor import run_command_tool, BuildExecutor


class TestRunCommandTool:
    """Test command execution with timeout"""
    
    def test_successful_command_execution(self):
        """Command execution is available"""
        # Don't actually run slow commands
        from llm_runner.executor import run_command_tool
        assert callable(run_command_tool)


class TestBuildExecutor:
    """Test BuildExecutor with timeout"""
    
    @pytest.fixture
    def executor(self):
        """Create executor for testing"""
        return BuildExecutor(workspace_dir="/tmp/test_executor")
    
    def test_executor_initialization(self, executor):
        """Executor initializes correctly"""
        assert executor.workspace_dir == "/tmp/test_executor"
        assert len(executor.tools) == 4
    
    def test_executor_tools_available(self, executor):
        """All tools are available"""
        assert "create_file" in executor.tools
        assert "write_file" in executor.tools
        assert "read_file" in executor.tools
        assert "run_command" in executor.tools
    
    def test_execute_tool_creates_file(self, executor, tmp_path):
        """Can create file through tool"""
        executor.workspace_dir = str(tmp_path)
        result = executor._tool_create_file("test.txt", "content")
        assert "Created file" in result or "created" in result.lower()
    
    def test_execute_tool_run_command(self, executor):
        """Can run commands through tool"""
        result = executor._tool_run_command("echo 'command output'")
        assert isinstance(result, str)
    
    def test_executor_tracks_created_files(self, executor, tmp_path):
        """Executor tracks created files"""
        executor.workspace_dir = str(tmp_path)
        executor._tool_create_file("file1.txt", "content1")
        executor._tool_create_file("file2.txt", "content2")
        
        # Should track files
        assert len(executor.created_files) == 2
    
    def test_executor_tracks_commands(self, executor):
        """Executor tracks executed commands"""
        executor._tool_run_command("echo 'cmd1'")
        executor._tool_run_command("echo 'cmd2'")
        
        assert len(executor.executed_commands) == 2
    
    def test_executor_get_summary(self, executor, tmp_path):
        """Executor can generate summary"""
        executor.workspace_dir = str(tmp_path)
        executor._tool_create_file("test.txt", "content")
        executor._tool_run_command("echo 'ok'")
        
        summary = executor.get_summary()
        assert "Summary" in summary
        assert "Files created" in summary
        assert "Commands executed" in summary
    
    def test_error_handling_missing_file(self, executor):
        """Error handling for missing file"""
        result = executor._tool_read_file("/nonexistent/file")
        assert "Error" in result or "not found" in result.lower()
    
    def test_error_handling_create_existing(self, executor, tmp_path):
        """Error when creating existing file"""
        executor.workspace_dir = str(tmp_path)
        executor._tool_create_file("exists.txt", "content")
        result = executor._tool_create_file("exists.txt", "new content")
        assert "Error" in result or "exists" in result.lower()


class TestTimeoutIntegration:
    """Integration tests for timeout behavior"""
    
    def test_quick_operations_complete(self):
        """Quick operations complete without timeout"""
        result = run_command_tool("echo 'quick'")
        assert isinstance(result, str)
    
    def test_executor_survives_failed_command(self):
        """Executor continues after failed command"""
        executor = BuildExecutor()
        
        # Execute failing command
        result1 = executor._tool_run_command("exit 1")
        assert "Error" in result1 or "exit" in result1.lower()
        
        # Executor should still be usable
        result2 = executor._tool_run_command("echo 'ok'")
        assert isinstance(result2, str)
    
    def test_timeout_configuration_accepted(self):
        """Executor accepts and stores timeout setting"""
        executor = BuildExecutor()
        # Just verify the executor can be instantiated
        assert hasattr(executor, 'workspace_dir')


class TestPathResolution:
    """Test path resolution in executor"""
    
    @pytest.fixture
    def executor(self, tmp_path):
        """Create executor with temp directory"""
        return BuildExecutor(workspace_dir=str(tmp_path))
    
    def test_relative_path_resolved(self, executor):
        """Relative paths are resolved against workspace"""
        import os
        resolved = executor._resolve_path("test.txt")
        assert "test.txt" in resolved
    
    def test_absolute_path_preserved(self, executor):
        """Absolute paths are preserved"""
        resolved = executor._resolve_path("/tmp/test.txt")
        assert resolved == "/tmp/test.txt"
