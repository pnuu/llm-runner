"""Tests for command history functionality"""
import pytest
import tempfile
from pathlib import Path
from llm_runner.history_manager import HistoryManager


class TestHistoryManager:
    """Test command history management"""
    
    def test_create_history_manager(self):
        """Test creating a history manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            assert manager is not None
    
    def test_add_to_history(self):
        """Test adding command to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            manager.add("Hello")
            
            assert manager.get_at_index(0) == "Hello"
    
    def test_history_persistence(self):
        """Test history persists to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history"
            
            manager1 = HistoryManager(history_file=history_file)
            manager1.add("Command 1")
            manager1.add("Command 2")
            
            # New manager should load history
            manager2 = HistoryManager(history_file=history_file)
            assert manager2.get_at_index(0) == "Command 1"
            assert manager2.get_at_index(1) == "Command 2"
    
    def test_get_history_count(self):
        """Test getting history count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("cmd1")
            manager.add("cmd2")
            manager.add("cmd3")
            
            assert manager.count() == 3
    
    def test_get_at_index(self):
        """Test retrieving history at index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("first")
            manager.add("second")
            manager.add("third")
            
            assert manager.get_at_index(0) == "first"
            assert manager.get_at_index(1) == "second"
            assert manager.get_at_index(2) == "third"
    
    def test_get_at_negative_index(self):
        """Test retrieving history with negative index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("a")
            manager.add("b")
            manager.add("c")
            
            assert manager.get_at_index(-1) == "c"  # Last
            assert manager.get_at_index(-2) == "b"  # Second to last
            assert manager.get_at_index(-3) == "a"  # Third to last
    
    def test_get_last_command(self):
        """Test getting last command"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("old")
            manager.add("new")
            
            assert manager.get_last() == "new"
    
    def test_search_history(self):
        """Test searching history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("list files")
            manager.add("edit config")
            manager.add("list users")
            manager.add("clear history")
            
            results = manager.search("list")
            assert len(results) == 2
            assert "list files" in results
            assert "list users" in results
    
    def test_clear_history(self):
        """Test clearing history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("cmd1")
            manager.add("cmd2")
            assert manager.count() == 2
            
            manager.clear()
            assert manager.count() == 0
    
    def test_get_all_history(self):
        """Test getting all history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("a")
            manager.add("b")
            manager.add("c")
            
            all_history = manager.get_all()
            assert len(all_history) == 3
            assert all_history == ["a", "b", "c"]
    
    def test_history_max_size(self):
        """Test history respects max size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history", max_size=5)
            
            for i in range(10):
                manager.add(f"cmd{i}")
            
            # Should only keep last 5
            assert manager.count() == 5
            assert manager.get_at_index(0) == "cmd5"  # First 5 removed
            assert manager.get_at_index(4) == "cmd9"  # Last added
    
    def test_remove_from_history(self):
        """Test removing item from history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("keep")
            manager.add("remove")
            manager.add("keep2")
            
            manager.remove("remove")
            
            assert manager.count() == 2
            all_hist = manager.get_all()
            assert "remove" not in all_hist
    
    def test_navigation_index(self):
        """Test navigation through history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("a")
            manager.add("b")
            manager.add("c")
            
            # Start at end
            manager.start_navigation()
            
            # Navigate backward
            assert manager.get_current() == "c"
            manager.navigate_up()
            assert manager.get_current() == "b"
            manager.navigate_up()
            assert manager.get_current() == "a"
            
            # Navigate forward
            manager.navigate_down()
            assert manager.get_current() == "b"
            manager.navigate_down()
            assert manager.get_current() == "c"
    
    def test_history_contains(self):
        """Test checking if history contains item"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("python script.py")
            manager.add("ls -la")
            
            assert manager.contains("python")
            assert manager.contains("ls")
            assert not manager.contains("ruby")
    
    def test_history_save_format(self):
        """Test history file format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history"
            
            manager = HistoryManager(history_file=history_file)
            manager.add("test command")
            manager.save()
            
            # Read file
            with open(history_file) as f:
                content = f.read()
            
            assert "test command" in content
    
    def test_duplicate_commands(self):
        """Test handling duplicate commands"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            manager.add("same")
            manager.add("same")
            manager.add("different")
            manager.add("same")
            
            # Should keep all occurrences
            assert manager.count() == 4
    
    def test_empty_history(self):
        """Test operations on empty history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            assert manager.count() == 0
            assert manager.get_all() == []
            assert manager.get_last() is None
            assert manager.search("anything") == []
    
    def test_history_with_special_chars(self):
        """Test history with special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(history_file=f"{tmpdir}/history")
            
            special = "echo 'Hello \"World\"' && echo $VAR"
            manager.add(special)
            
            assert manager.get_last() == special
            assert manager.contains("Hello")
