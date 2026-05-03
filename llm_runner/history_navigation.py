"""Interactive command line editor with readline-style history navigation"""
from pathlib import Path
from typing import Optional, List
from llm_runner.history_manager import HistoryManager


class CommandLineEditor:
    """Provides readline-style command line editing with up/down history navigation"""
    
    def __init__(self, history_file: Optional[str] = None, max_history: int = 1000):
        """Initialize editor with history support
        
        Args:
            history_file: Path to history file (default: ~/.llm_runner/command_history)
            max_history: Maximum history size
        """
        if history_file is None:
            history_file = str(Path.home() / ".llm_runner" / "command_history")
        
        self.history = HistoryManager(history_file=history_file, max_size=max_history)
        self.nav_index = None
    
    def input(self, prompt: str = "") -> str:
        """Get user input with history support
        
        Args:
            prompt: Prompt to display
            
        Returns:
            User input line
        """
        # Python's built-in input() doesn't support up/down arrows directly
        # In a real CLI, this would use readline/prompt_toolkit
        # For now, we use standard input and history management
        line = input(prompt)
        if line.strip():
            self.add_to_history(line)
        return line
    
    def add_to_history(self, command: str) -> None:
        """Add command to history
        
        Args:
            command: Command to add
        """
        self.history.add(command)
    
    def start_navigation(self) -> None:
        """Start navigating history (like pressing up arrow)"""
        self.history.start_navigation()
        self.nav_index = len(self.history.get_all()) - 1
    
    def move_up(self) -> None:
        """Move to previous command in history"""
        if self.nav_index is None:
            self.start_navigation()
        
        if self.nav_index > 0:
            self.nav_index -= 1
    
    def move_down(self) -> None:
        """Move to next command in history"""
        if self.nav_index is None:
            return
        
        max_idx = len(self.history.get_all()) - 1
        if self.nav_index < max_idx:
            self.nav_index += 1
    
    def current(self) -> Optional[str]:
        """Get current command in navigation"""
        if self.nav_index is None:
            return None
        
        all_history = self.history.get_all()
        if 0 <= self.nav_index < len(all_history):
            return all_history[self.nav_index]
        return None
    
    def end_navigation(self) -> None:
        """End navigation mode"""
        self.nav_index = None
        self.history.end_navigation()
    
    def search(self, pattern: str) -> List[str]:
        """Search history by pattern
        
        Args:
            pattern: Search pattern
            
        Returns:
            List of matching commands
        """
        return self.history.search(pattern)
    
    def search_backward(self, pattern: str) -> Optional[str]:
        """Search backward in history (most recent first)
        
        Args:
            pattern: Search pattern
            
        Returns:
            Most recent matching command or None
        """
        results = self.search(pattern)
        return results[-1] if results else None
    
    def clear_history(self) -> None:
        """Clear all history"""
        self.history.clear()
        self.nav_index = None
    
    def history_count(self) -> int:
        """Get number of commands in history
        
        Returns:
            History size
        """
        return self.history.count()
    
    def get_history(self) -> List[str]:
        """Get all history
        
        Returns:
            List of all commands
        """
        return self.history.get_all()
