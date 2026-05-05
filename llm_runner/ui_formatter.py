"""UI formatting for interactive chat with color support"""
import re
from typing import Optional, Dict


# Map color names to ANSI codes
NAMED_COLORS = {
    # Basic colors
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    
    # Bright colors
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    
    # Gray variants
    "dark_gray": "\033[90m",      # Same as bright_black
    "light_gray": "\033[37m",     # Same as white
    "gray": "\033[90m",           # Alias for dark gray
    
    # CSS-like names
    "silver": "\033[37m",
    "maroon": "\033[31m",
    "purple": "\033[35m",
    "navy": "\033[34m",
    "teal": "\033[36m",
    "olive": "\033[33m",
    "lime": "\033[32m",
}

# ANSI reset code
RESET = "\033[0m"


def parse_color(color_spec: Optional[str]) -> str:
    """Parse color specification and return ANSI code.
    
    Supports:
    - Hex colors: #ffffff, #000000
    - Plain color names: white, black, red, etc.
    - CSS color names: silver, navy, etc.
    
    Args:
        color_spec: Color specification (hex, name, or None)
    
    Returns:
        ANSI color code string (defaults to white if invalid)
    """
    if not color_spec:
        return NAMED_COLORS.get("white", "\033[37m")
    
    # Normalize input
    color_spec = str(color_spec).strip()
    
    # Try as hex color first
    if color_spec.startswith("#"):
        hex_code = color_spec.lstrip("#")
        if len(hex_code) == 6 and all(c in "0123456789abcdefABCDEF" for c in hex_code):
            # Convert hex to RGB
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            # Use approximate ANSI 256-color code
            # Simplified: just return a standard color based on brightness
            brightness = (r + g + b) / 3
            if brightness > 200:
                return NAMED_COLORS.get("white", "\033[37m")
            elif brightness > 100:
                return NAMED_COLORS.get("light_gray", "\033[37m")
            else:
                return NAMED_COLORS.get("black", "\033[30m")
    
    # Try as hex without #
    if len(color_spec) == 6 and all(c in "0123456789abcdefABCDEF" for c in color_spec):
        r = int(color_spec[0:2], 16)
        g = int(color_spec[2:4], 16)
        b = int(color_spec[4:6], 16)
        brightness = (r + g + b) / 3
        if brightness > 200:
            return NAMED_COLORS.get("white", "\033[37m")
        elif brightness > 100:
            return NAMED_COLORS.get("light_gray", "\033[37m")
        else:
            return NAMED_COLORS.get("black", "\033[30m")
    
    # Try as color name
    color_lower = color_spec.lower()
    if color_lower in NAMED_COLORS:
        return NAMED_COLORS[color_lower]
    
    # Try with underscores replaced with spaces
    color_with_spaces = color_lower.replace("_", " ")
    if color_with_spaces in {k.replace("_", " "): v for k, v in NAMED_COLORS.items()}:
        # Find the matching key
        for key, val in NAMED_COLORS.items():
            if key.replace("_", " ") == color_with_spaces:
                return val
    
    # Default to white if not found
    return NAMED_COLORS.get("white", "\033[37m")


class ChatUIFormatter:
    """Format chat messages and UI elements with color support."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize formatter with color config.
        
        Args:
            config: Dict with 'user_message', 'ai_message', 'status_line' colors
        """
        if config is None:
            config = {}
        
        self.user_color = parse_color(config.get("user_message", "light_gray"))
        self.ai_color = parse_color(config.get("ai_message", "white"))
        self.status_color = parse_color(config.get("status_line", "cyan"))
        self.command_color = parse_color(config.get("command_window", "white"))
    
    def format_user_message(self, text: str) -> str:
        """Format user message with color.
        
        Args:
            text: User message text
        
        Returns:
            Colored message string
        """
        if not text:
            return text
        
        return f"{self.user_color}{text}{RESET}"
    
    def format_ai_message(self, text: str) -> str:
        """Format AI message with color.
        
        Args:
            text: AI response text
        
        Returns:
            Colored message string
        """
        if not text:
            return text
        
        return f"{self.ai_color}{text}{RESET}"
    
    def format_status_line(self, model: str, mode: str, context_percent: int) -> str:
        """Format status line with model, mode, and context info.
        
        Args:
            model: Current model name
            mode: Current mode (interactive, plan, build, etc.)
            context_percent: Context usage percentage (0-100)
        
        Returns:
            Formatted status line
        """
        status = f"[model: {model}] [mode: {mode}] [context: {context_percent}%]"
        return f"{self.status_color}{status}{RESET}"
    
    def format_command_prompt(self) -> str:
        """Format command input prompt.
        
        Returns:
            Prompt string
        """
        return f"{self.command_color}> {RESET}"
    
    def format_separator(self) -> str:
        """Format visual separator.
        
        Returns:
            Separator line
        """
        return f"{self.status_color}{'─' * 60}{RESET}"


def disable_ansi_if_needed():
    """Disable ANSI codes if terminal doesn't support them.
    
    This is a utility function that can be called to detect
    terminal capabilities and disable ANSI if needed.
    """
    try:
        import os
        import sys
        
        # Check if NO_COLOR env var is set
        if os.environ.get("NO_COLOR"):
            _disable_ansi_codes()
        
        # Check if terminal is dumb
        if os.environ.get("TERM") == "dumb":
            _disable_ansi_codes()
        
        # On Windows, try to enable ANSI support
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)  # stdout
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    kernel32.SetConsoleMode(handle, mode)
            except Exception:
                pass
    except Exception:
        pass


def _disable_ansi_codes():
    """Disable ANSI codes globally."""
    global NAMED_COLORS, RESET
    
    # Replace all ANSI codes with empty strings
    NAMED_COLORS = {k: "" for k in NAMED_COLORS}
    RESET = ""
