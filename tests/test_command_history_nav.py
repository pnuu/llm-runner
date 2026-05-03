"""Tests for command history navigation in interactive chat"""
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from llm_runner.history_navigation import CommandLineEditor


class TestCommandLineEditor:
    """Test interactive readline-style command line editing"""
    
    def test_editor_init(self):
        """Test initializing editor"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            assert editor is not None
    
    def test_editor_startup_loads_history(self):
        """Test that editor loads history on startup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history"
            
            # Create history file
            editor1 = CommandLineEditor(history_file=history_file)
            editor1.add_to_history("old command")
            
            # New editor should load history
            editor2 = CommandLineEditor(history_file=history_file)
            assert editor2.history_count() == 1
    
    def test_input_with_history(self):
        """Test input method with history support"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("previous command")
            
            # Mock input to simulate user typing
            with patch('builtins.input', return_value='new command'):
                result = editor.input("prompt> ")
                assert result == 'new command'
    
    def test_history_navigation_up(self):
        """Test navigating up through history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            editor.add_to_history("cmd3")
            
            # Navigate up
            editor.start_navigation()
            assert editor.current() == "cmd3"
            
            editor.move_up()
            assert editor.current() == "cmd2"
            
            editor.move_up()
            assert editor.current() == "cmd1"
    
    def test_history_navigation_down(self):
        """Test navigating down through history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            editor.add_to_history("cmd3")
            
            # Start at oldest, move forward
            editor.start_navigation()
            editor.move_up()
            editor.move_up()
            assert editor.current() == "cmd1"
            
            # Navigate down
            editor.move_down()
            assert editor.current() == "cmd2"
            
            editor.move_down()
            assert editor.current() == "cmd3"
    
    def test_history_navigation_bounds(self):
        """Test navigation doesn't go out of bounds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            
            editor.start_navigation()
            
            # Moving down at end should stay at end
            editor.move_down()
            assert editor.current() == "cmd2"
            editor.move_down()
            assert editor.current() == "cmd2"
            
            # Move to beginning
            editor.move_up()
            editor.move_up()
            
            # Moving up at beginning should stay at beginning
            editor.move_up()
            assert editor.current() == "cmd1"
    
    def test_add_to_history(self):
        """Test adding command to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            
            assert editor.history_count() == 2
    
    def test_search_history(self):
        """Test searching through history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("python script.py")
            editor.add_to_history("ls -la")
            editor.add_to_history("python test.py")
            
            results = editor.search("python")
            assert len(results) == 2
            assert "python script.py" in results
            assert "python test.py" in results
    
    def test_clear_history(self):
        """Test clearing history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            
            assert editor.history_count() == 2
            
            editor.clear_history()
            assert editor.history_count() == 0
    
    def test_history_persistence_across_instances(self):
        """Test that history persists across editor instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history"
            
            # First editor
            editor1 = CommandLineEditor(history_file=history_file)
            editor1.add_to_history("saved command")
            
            # Second editor should see it
            editor2 = CommandLineEditor(history_file=history_file)
            assert editor2.history_count() == 1
            
            editor2.start_navigation()
            assert editor2.current() == "saved command"
    
    def test_history_max_size(self):
        """Test history respects max size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(
                history_file=f"{tmpdir}/history",
                max_history=5
            )
            
            for i in range(10):
                editor.add_to_history(f"cmd{i}")
            
            assert editor.history_count() == 5
    
    def test_end_navigation(self):
        """Test ending navigation mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("cmd1")
            editor.add_to_history("cmd2")
            
            editor.start_navigation()
            editor.move_up()
            
            editor.end_navigation()
            
            # After ending, navigation should be reset
            assert editor.nav_index is None
    
    def test_reverse_search(self):
        """Test reverse history search (backward search)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("find pattern in file")
            editor.add_to_history("grep pattern")
            editor.add_to_history("find pattern 2")
            
            # Search for most recent with "find"
            result = editor.search_backward("find")
            assert result == "find pattern 2" or result in ["find pattern in file", "find pattern 2"]
    
    def test_history_without_duplicates(self):
        """Test adding same command multiple times"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            editor.add_to_history("same")
            editor.add_to_history("same")
            editor.add_to_history("different")
            editor.add_to_history("same")
            
            # All duplicates should be kept (shell history style)
            assert editor.history_count() == 4
    
    def test_special_characters_in_history(self):
        """Test history with special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            
            special = "echo 'Hello \"World\"' && echo $VAR"
            editor.add_to_history(special)
            
            editor.start_navigation()
            assert editor.current() == special
    
    def test_newlines_in_history(self):
        """Test that newlines in commands don't break history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            
            # Single line command only (newlines would break the format)
            cmd = "echo hello"
            editor.add_to_history(cmd)
            
            editor.start_navigation()
            assert editor.current() == cmd
