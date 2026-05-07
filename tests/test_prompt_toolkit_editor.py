"""Tests for PromptToolkitEditor with prompt_toolkit integration"""
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from llm_runner.history_navigation import PromptToolkitEditor, HAS_PROMPT_TOOLKIT


@pytest.mark.skipif(not HAS_PROMPT_TOOLKIT, reason="prompt_toolkit not installed")
class TestPromptToolkitEditor:
    """Test PromptToolkitEditor with full readline support"""
    
    def test_editor_init(self):
        """Test initializing PromptToolkitEditor"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            assert editor is not None
            assert hasattr(editor, 'session')
            assert hasattr(editor, 'file_history')
    
    def test_editor_has_prompt_toolkit_attributes(self):
        """Test that editor has prompt_toolkit attributes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            # Should have PromptSession and FileHistory
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            
            assert isinstance(editor.session, PromptSession)
            assert isinstance(editor.file_history, FileHistory)
    
    def test_editor_add_to_history(self):
        """Test adding commands to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("test command 1")
            editor.add_to_history("test command 2")
            
            assert editor.history_count() == 2
    
    def test_editor_history_search(self):
        """Test searching history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("list all files")
            editor.add_to_history("list directories")
            editor.add_to_history("show history")
            
            results = editor.search("list")
            assert len(results) == 2
            assert "list all files" in results
            assert "list directories" in results
    
    def test_editor_history_persistence(self):
        """Test that history persists across instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history"
            
            # Create editor 1 and add commands
            editor1 = PromptToolkitEditor(history_file=history_file)
            editor1.add_to_history("old command")
            
            # Create editor 2 and verify history is loaded
            editor2 = PromptToolkitEditor(history_file=history_file)
            assert editor2.history_count() == 1
            assert editor2.get_history()[0] == "old command"
    
    def test_editor_backward_search(self):
        """Test reverse search (most recent first)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("old command")
            editor.add_to_history("newer command")
            editor.add_to_history("newest command")
            
            # Search should return most recent match
            result = editor.search_backward("command")
            assert result == "newest command"
    
    def test_editor_clear_history(self):
        """Test clearing history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            
            assert editor.history_count() == 2
            editor.clear_history()
            assert editor.history_count() == 0
    
    def test_editor_input_with_mock_prompt(self):
        """Test input method with mocked prompt session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            # Mock the session.prompt method
            with patch.object(editor.session, 'prompt', return_value='test input'):
                result = editor.input("prompt> ")
                assert result == "test input"
                assert editor.history_count() == 1
    
    def test_editor_input_empty_not_added_to_history(self):
        """Test that empty input is not added to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            with patch.object(editor.session, 'prompt', return_value=''):
                result = editor.input("prompt> ")
                assert result == ""
                assert editor.history_count() == 0
    
    def test_editor_input_whitespace_only_not_added(self):
        """Test that whitespace-only input is not added to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            with patch.object(editor.session, 'prompt', return_value='   \t  '):
                result = editor.input("prompt> ")
                assert editor.history_count() == 0
    
    def test_editor_navigation_methods(self):
        """Test navigation API compatibility"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            # These should not raise errors (API compatibility)
            editor.start_navigation()
            editor.end_navigation()
    
    def test_editor_multi_line_command_support(self):
        """Test that editor can handle multi-line commands"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            # Simulate a multi-line command
            multiline_cmd = "line1\nline2\nline3"
            with patch.object(editor.session, 'prompt', return_value=multiline_cmd):
                result = editor.input("prompt> ")
                assert result == multiline_cmd
                assert editor.history_count() == 1
    
    def test_editor_readline_features(self):
        """Test that PromptToolkitEditor provides readline-style features"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = PromptToolkitEditor(history_file=f"{tmpdir}/history")
            
            # Verify EMACS editing mode is set (provides readline-style keys)
            from prompt_toolkit.enums import EditingMode
            assert editor.session.editing_mode == EditingMode.EMACS
            
            # Verify history search is enabled
            assert editor.session.enable_history_search is True
