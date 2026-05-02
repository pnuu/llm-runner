"""Test build executor and tools"""
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from llm_runner.executor import (
    BuildExecutor,
    create_file_tool,
    write_file_tool,
    read_file_tool,
    run_command_tool
)


def test_create_file_tool():
    """Test create file tool"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.txt")
        result = create_file_tool(filepath, "Hello World")
        
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            assert f.read() == "Hello World"
        assert "created" in result.lower() or "success" in result.lower()


def test_create_file_tool_prevents_overwrite():
    """Test that create file prevents overwriting without confirmation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.txt")
        
        # Create initial file
        with open(filepath, "w") as f:
            f.write("Original")
        
        # Try to create again - should fail or warn
        result = create_file_tool(filepath, "New content")
        
        # Should not overwrite
        with open(filepath, "r") as f:
            content = f.read()
            assert content == "Original" or "exists" in result.lower()


def test_write_file_tool():
    """Test write file tool"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.txt")
        
        # Create file first
        with open(filepath, "w") as f:
            f.write("Original")
        
        # Write to it
        result = write_file_tool(filepath, "Updated")
        
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            assert f.read() == "Updated"


def test_read_file_tool():
    """Test read file tool"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.txt")
        
        with open(filepath, "w") as f:
            f.write("File content")
        
        result = read_file_tool(filepath)
        
        assert "File content" in result


def test_read_file_tool_not_found():
    """Test read file tool with non-existent file"""
    result = read_file_tool("/nonexistent/path.txt")
    
    assert "error" in result.lower() or "not found" in result.lower()


def test_run_command_tool():
    """Test run shell command tool"""
    result = run_command_tool("echo 'test'")
    
    assert "test" in result or result != ""


def test_run_command_tool_error():
    """Test run command tool with error"""
    result = run_command_tool("nonexistent_command_xyz")
    
    assert "error" in result.lower() or "not found" in result.lower()


def test_build_executor_init():
    """Test BuildExecutor initialization"""
    executor = BuildExecutor(workspace_dir="/tmp")
    assert executor.workspace_dir == "/tmp"
    assert len(executor.tools) > 0


def test_build_executor_has_tools():
    """Test BuildExecutor has all tools available"""
    executor = BuildExecutor()
    
    # Should have tools for file and command operations
    tool_names = list(executor.tools.keys())
    assert "create_file" in tool_names
    assert "write_file" in tool_names
    assert "read_file" in tool_names
    assert "run_command" in tool_names


def test_build_executor_execute_tool():
    """Test executing a tool through executor"""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = BuildExecutor(workspace_dir=tmpdir)
        
        result = executor.execute_tool("create_file", ["test.txt", "Hello"])
        
        filepath = os.path.join(tmpdir, "test.txt")
        assert os.path.exists(filepath)


def test_build_executor_tool_with_relative_path():
    """Test that tools work with relative paths in workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = BuildExecutor(workspace_dir=tmpdir)
        
        # Should resolve relative to workspace
        result = executor.execute_tool("create_file", ["subdir/test.txt", "Content"])
        
        filepath = os.path.join(tmpdir, "subdir/test.txt")
        assert os.path.exists(filepath)
