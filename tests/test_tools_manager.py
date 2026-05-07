"""Tests for tool calling system"""
import pytest
import tempfile
import os
from pathlib import Path
from llm_runner.tools_manager import FileWriteTool, ToolsManager, ToolResult, create_tools_manager


class TestFileWriteTool:
    """Test FileWriteTool"""
    
    def test_file_write_basic(self):
        """Test basic file writing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "test.txt")
            
            result = tool.execute(filepath, "Hello World")
            
            assert result.success
            assert "Created file" in result.message
            assert os.path.exists(filepath)
            
            with open(filepath) as f:
                assert f.read() == "Hello World"
    
    def test_file_write_creates_directories(self):
        """Test that parent directories are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "subdir", "file.txt")
            
            result = tool.execute(filepath, "Content")
            
            assert result.success
            assert os.path.exists(filepath)
    
    def test_file_write_overwrite(self):
        """Test overwriting existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "test.txt")
            
            # Write first time
            tool.execute(filepath, "Old content")
            
            # Write second time (should overwrite)
            result = tool.execute(filepath, "New content")
            
            assert result.success
            with open(filepath) as f:
                assert f.read() == "New content"
    
    def test_file_write_append(self):
        """Test appending to existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "test.txt")
            
            # Write first time
            tool.execute(filepath, "Line 1\n")
            
            # Append
            result = tool.execute(filepath, "Line 2\n", append=True)
            
            assert result.success
            with open(filepath) as f:
                content = f.read()
                assert "Line 1" in content
                assert "Line 2" in content
    
    def test_file_write_unsafe_path(self):
        """Test that unsafe paths are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            
            # Try to write outside allowed directory
            result = tool.execute("/etc/passwd", "hacked")
            
            assert not result.success
            assert "outside allowed directories" in result.message
    
    def test_file_write_empty_content(self):
        """Test writing empty content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "empty.txt")
            
            result = tool.execute(filepath, "")
            
            assert result.success
            with open(filepath) as f:
                assert f.read() == ""
    
    def test_file_write_unicode_content(self):
        """Test writing unicode content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "unicode.txt")
            content = "Hello 世界 🌍 Привет"
            
            result = tool.execute(filepath, content)
            
            assert result.success
            with open(filepath, encoding='utf-8') as f:
                assert f.read() == content


class TestToolsManager:
    """Test ToolsManager"""
    
    def test_tools_manager_init(self):
        """Test tools manager initialization"""
        manager = ToolsManager()
        assert manager is not None
        assert "write_file" in manager.tools
    
    def test_get_tools_description(self):
        """Test getting tools description"""
        manager = ToolsManager()
        desc = manager.get_tools_description()
        
        assert "write_file" in desc
        assert "Available tools" in desc or "Tool:" in desc
        assert "write_file" in desc
    
    def test_parse_tool_calls_single(self):
        """Test parsing single tool call"""
        manager = ToolsManager()
        response = 'I will write a file. <tool name="write_file"><path>test.txt</path><content>Hello</content></tool>'
        
        calls = manager.parse_tool_calls(response)
        
        assert len(calls) == 1
        assert calls[0]["name"] == "write_file"
        assert calls[0]["params"]["path"] == "test.txt"
        assert calls[0]["params"]["content"] == "Hello"
    
    def test_parse_tool_calls_multiple(self):
        """Test parsing multiple tool calls"""
        manager = ToolsManager()
        response = '''
        <tool name="write_file"><path>file1.txt</path><content>Content 1</content></tool>
        Some text here.
        <tool name="write_file"><path>file2.txt</path><content>Content 2</content></tool>
        '''
        
        calls = manager.parse_tool_calls(response)
        
        assert len(calls) == 2
        assert calls[0]["params"]["path"] == "file1.txt"
        assert calls[1]["params"]["path"] == "file2.txt"
    
    def test_parse_tool_calls_with_append(self):
        """Test parsing tool call with append parameter"""
        manager = ToolsManager()
        response = '<tool name="write_file"><path>test.txt</path><content>More content</content><append>true</append></tool>'
        
        calls = manager.parse_tool_calls(response)
        
        assert len(calls) == 1
        assert calls[0]["params"]["append"] == "true"
    
    def test_parse_tool_calls_none(self):
        """Test parsing response with no tool calls"""
        manager = ToolsManager()
        response = "This is just a normal response with no tool calls."
        
        calls = manager.parse_tool_calls(response)
        
        assert len(calls) == 0
    
    def test_execute_tool_write_file(self):
        """Test executing write_file tool"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolsManager(allowed_dirs=[tmpdir])
            
            result = manager.execute_tool("write_file", {
                "path": os.path.join(tmpdir, "test.txt"),
                "content": "Hello World"
            })
            
            assert result.success
            assert "Created file" in result.message
    
    def test_execute_tool_unknown(self):
        """Test executing unknown tool"""
        manager = ToolsManager()
        
        result = manager.execute_tool("unknown_tool", {})
        
        assert not result.success
        assert "Unknown tool" in result.message
    
    def test_execute_tool_calls_full_flow(self):
        """Test full flow of parsing and executing tool calls"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolsManager(allowed_dirs=[tmpdir])
            filepath = os.path.join(tmpdir, "poem.txt")
            
            response = f'''I'll write a poem for you:
            <tool name="write_file"><path>{filepath}</path><content>Roses are red
            Violets are blue
            Tool calling works
            Now we're through!</content></tool>
            The poem has been written to {filepath}!'''
            
            results, cleaned_response = manager.execute_tool_calls(response)
            
            assert len(results) == 1
            assert results[0].success
            assert os.path.exists(filepath)
            assert "tool" not in cleaned_response.lower() or "<" not in cleaned_response
    
    def test_tool_result_repr(self):
        """Test ToolResult string representation"""
        result = ToolResult(True, "File written successfully")
        
        str_repr = str(result)
        assert "SUCCESS" in str_repr
        assert "File written successfully" in str_repr
        
        error_result = ToolResult(False, "File not found")
        error_repr = str(error_result)
        assert "ERROR" in error_repr
    
    def test_create_tools_manager_function(self):
        """Test convenience function"""
        manager = create_tools_manager()
        
        assert manager is not None
        assert isinstance(manager, ToolsManager)


class TestToolsManagerIntegration:
    """Integration tests for tool calling"""
    
    def test_model_response_with_tool_call(self):
        """Test handling model response with tool call"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolsManager(allowed_dirs=[tmpdir])
            
            # Simulate model response
            model_response = f'''Sure! Here's a short story for you.

<tool name="write_file"><path>{tmpdir}/story.txt</path><content>Once upon a time, there was a tool that could write files.</content></tool>

I've saved the story to story.txt!'''
            
            # Parse and execute
            results, cleaned = manager.execute_tool_calls(model_response)
            
            # Verify tool was executed
            assert len(results) == 1
            assert results[0].success
            
            # Verify file was created
            filepath = os.path.join(tmpdir, "story.txt")
            assert os.path.exists(filepath)
            with open(filepath) as f:
                assert "Once upon a time" in f.read()
            
            # Verify response is cleaned
            assert "<tool" not in cleaned.lower()
            assert "I've saved the story" in cleaned
    
    def test_multiple_files_creation(self):
        """Test creating multiple files in one response"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolsManager(allowed_dirs=[tmpdir])
            
            response = f'''I'll create three files for you:

<tool name="write_file"><path>{tmpdir}/file1.txt</path><content>Content 1</content></tool>
<tool name="write_file"><path>{tmpdir}/file2.txt</path><content>Content 2</content></tool>
<tool name="write_file"><path>{tmpdir}/file3.txt</path><content>Content 3</content></tool>

All done!'''
            
            results, _ = manager.execute_tool_calls(response)
            
            assert len(results) == 3
            assert all(r.success for r in results)
            
            for i in range(1, 4):
                assert os.path.exists(os.path.join(tmpdir, f"file{i}.txt"))
    
    def test_system_prompt_extension(self):
        """Test system prompt extension"""
        manager = ToolsManager()
        extension = manager.get_system_prompt_extension()
        
        assert "tool" in extension.lower()
        assert "write_file" in extension
        assert "format" in extension.lower() or "example" in extension.lower()


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_malformed_tool_call(self):
        """Test handling malformed tool call"""
        manager = ToolsManager()
        
        # Missing closing tag
        response = '<tool name="write_file"><path>test.txt'
        calls = manager.parse_tool_calls(response)
        
        assert len(calls) == 0
    
    def test_tool_call_with_special_chars(self):
        """Test tool call with special characters in content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ToolsManager(allowed_dirs=[tmpdir])
            
            content = "Line 1<>&\"'Line 2"
            response = f'<tool name="write_file"><path>{tmpdir}/special.txt</path><content>{content}</content></tool>'
            
            results, _ = manager.execute_tool_calls(response)
            
            assert len(results) == 1
            # May or may not succeed depending on XML parsing, but shouldn't crash
    
    def test_large_file_write(self):
        """Test writing a large file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileWriteTool(allowed_dirs=[tmpdir])
            
            # Create 1MB content
            large_content = "x" * (1024 * 1024)
            filepath = os.path.join(tmpdir, "large.txt")
            
            result = tool.execute(filepath, large_content)
            
            assert result.success
            assert os.path.getsize(filepath) >= 1024 * 1024
