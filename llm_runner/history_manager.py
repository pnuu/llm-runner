"""Command history management module"""
from pathlib import Path
from typing import List, Optional


class HistoryManager:
    """Manages command history with persistence"""
    
    def __init__(self, history_file: Optional[str] = None, max_size: int = 1000):
        """Initialize history manager
        
        Args:
            history_file: Path to history file (default: ~/.llm_runner/history)
            max_size: Maximum history size before pruning oldest
        """
        if history_file is None:
            history_file = str(Path.home() / ".llm_runner" / "history")
        
        self.history_file = Path(history_file)
        self.max_size = max_size
        self.history = []
        self.nav_index = None  # For navigation mode
        
        # Create parent directories
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self._load()
    
    def add(self, command: str) -> None:
        """Add command to history
        
        Args:
            command: Command to add
        """
        if command and command.strip():  # Don't add empty
            self.history.append(command)
            self._prune()
            self.save()
    
    def _prune(self) -> None:
        """Keep history within max_size"""
        if len(self.history) > self.max_size:
            self.history = self.history[-self.max_size:]
    
    def get_at_index(self, index: int) -> Optional[str]:
        """Get command at index
        
        Args:
            index: Index (supports negative indexing)
            
        Returns:
            Command string or None if index out of range
        """
        try:
            return self.history[index]
        except IndexError:
            return None
    
    def get_last(self) -> Optional[str]:
        """Get last command
        
        Returns:
            Last command or None
        """
        return self.history[-1] if self.history else None
    
    def get_all(self) -> List[str]:
        """Get all history
        
        Returns:
            List of all commands
        """
        return self.history.copy()
    
    def count(self) -> int:
        """Get history count
        
        Returns:
            Number of commands in history
        """
        return len(self.history)
    
    def search(self, pattern: str) -> List[str]:
        """Search history by pattern
        
        Args:
            pattern: Search pattern (substring match)
            
        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.history if pattern.lower() in cmd.lower()]
    
    def contains(self, pattern: str) -> bool:
        """Check if history contains pattern
        
        Args:
            pattern: Search pattern
            
        Returns:
            True if pattern found
        """
        return any(pattern.lower() in cmd.lower() for cmd in self.history)
    
    def remove(self, command: str) -> None:
        """Remove all occurrences of command
        
        Args:
            command: Command to remove
        """
        self.history = [c for c in self.history if c != command]
        self.save()
    
    def clear(self) -> None:
        """Clear all history"""
        self.history = []
        self.save()
    
    def save(self) -> None:
        """Save history to file"""
        with open(self.history_file, 'w') as f:
            for cmd in self.history:
                f.write(cmd + '\n')
    
    def _load(self) -> None:
        """Load history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = [line.rstrip('\n') for line in f if line.strip()]
    
    # Navigation support for readline-style up/down arrows
    
    def start_navigation(self) -> None:
        """Start navigation mode (arrow keys)"""
        self.nav_index = len(self.history) - 1
    
    def navigate_up(self) -> None:
        """Navigate to previous command (up arrow)"""
        if self.nav_index is not None and self.nav_index > 0:
            self.nav_index -= 1
    
    def navigate_down(self) -> None:
        """Navigate to next command (down arrow)"""
        if self.nav_index is not None and self.nav_index < len(self.history) - 1:
            self.nav_index += 1
    
    def get_current(self) -> Optional[str]:
        """Get current navigation item
        
        Returns:
            Current command or None
        """
        if self.nav_index is not None and 0 <= self.nav_index < len(self.history):
            return self.history[self.nav_index]
        return None
    
    def end_navigation(self) -> None:
        """End navigation mode"""
        self.nav_index = None
