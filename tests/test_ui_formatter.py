"""Tests for UI formatter and color handling"""
import pytest
from llm_runner.ui_formatter import ChatUIFormatter, parse_color, NAMED_COLORS


class TestColorParsing:
    """Test color parsing from various formats"""
    
    def test_parse_hex_color_standard(self):
        """Test parsing standard hex color codes"""
        assert parse_color("#ffffff") is not None
        assert parse_color("#000000") is not None
        assert parse_color("#ff0000") is not None
    
    def test_parse_hex_color_lowercase(self):
        """Test hex colors with lowercase letters"""
        color = parse_color("#abcdef")
        assert color is not None
    
    def test_parse_hex_color_uppercase(self):
        """Test hex colors with uppercase letters"""
        color = parse_color("#ABCDEF")
        assert color is not None
    
    def test_parse_plain_color_names(self):
        """Test parsing plain English color names"""
        for name in ["white", "black", "red", "green", "blue", "yellow", "cyan", "magenta", "light_gray", "dark_gray"]:
            color = parse_color(name)
            assert color is not None, f"Failed to parse color: {name}"
    
    def test_parse_plain_color_names_case_insensitive(self):
        """Test that color names are case insensitive"""
        color1 = parse_color("white")
        color2 = parse_color("WHITE")
        color3 = parse_color("White")
        assert color1 == color2 == color3
    
    def test_parse_invalid_hex_returns_default(self):
        """Test that invalid hex colors return default"""
        # Invalid hex length
        color = parse_color("#fff")  # Should be 6 digits
        assert color is not None  # Should return default, not crash
    
    def test_parse_invalid_color_returns_default(self):
        """Test that invalid color names return default"""
        color = parse_color("invalid_color_name")
        assert color is not None  # Should return default
    
    def test_parse_empty_string_returns_default(self):
        """Test that empty string returns default"""
        color = parse_color("")
        assert color is not None
    
    def test_parse_none_returns_default(self):
        """Test that None returns default"""
        color = parse_color(None)
        assert color is not None


class TestChatUIFormatter:
    """Test ChatUIFormatter class"""
    
    def test_formatter_initialization_defaults(self):
        """Test formatter initializes with defaults"""
        formatter = ChatUIFormatter({})
        assert formatter is not None
        assert formatter.user_color is not None
        assert formatter.ai_color is not None
    
    def test_formatter_initialization_custom_colors(self):
        """Test formatter with custom color config"""
        config = {
            "user_message": "yellow",
            "ai_message": "cyan",
            "status_line": "green"
        }
        formatter = ChatUIFormatter(config)
        assert formatter is not None
        assert formatter.user_color is not None
        assert formatter.ai_color is not None
        assert formatter.status_color is not None
    
    def test_format_user_message(self):
        """Test formatting user message"""
        formatter = ChatUIFormatter({})
        text = "Hello, how are you?"
        formatted = formatter.format_user_message(text)
        
        # Should contain the text
        assert text in formatted
        # Should have ANSI codes
        assert "\033[" in formatted or "Light" in formatted or len(formatted) > len(text)
    
    def test_format_ai_message(self):
        """Test formatting AI message"""
        formatter = ChatUIFormatter({})
        text = "I am doing well, thank you!"
        formatted = formatter.format_ai_message(text)
        
        # Should contain the text
        assert text in formatted
        # Should have ANSI codes or color info
        assert "\033[" in formatted or "White" in formatted or len(formatted) > len(text)
    
    def test_format_user_message_preserves_content(self):
        """Test that formatting preserves message content"""
        formatter = ChatUIFormatter({})
        original = "This is a test message with special chars: !@#$%"
        formatted = formatter.format_user_message(original)
        
        # Content should be in the formatted string
        assert original in formatted
    
    def test_format_ai_message_preserves_content(self):
        """Test that formatting preserves AI message content"""
        formatter = ChatUIFormatter({})
        original = "Response with numbers 123 and punctuation..."
        formatted = formatter.format_ai_message(original)
        
        # Content should be in the formatted string
        assert original in formatted
    
    def test_format_status_line(self):
        """Test status line formatting"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=42
        )
        
        # Should contain all components
        assert "mistral:7b" in status
        assert "interactive" in status
        assert "42" in status
    
    def test_format_status_line_max_context(self):
        """Test status line with 100% context"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="llama3:8b",
            mode="chat",
            context_percent=100
        )
        
        assert "llama3:8b" in status
        assert "100" in status
    
    def test_format_status_line_zero_context(self):
        """Test status line with 0% context"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="neural-chat",
            mode="interactive",
            context_percent=0
        )
        
        assert "neural-chat" in status
        assert "0" in status
    
    def test_format_command_prompt(self):
        """Test command prompt formatting"""
        formatter = ChatUIFormatter({})
        prompt = formatter.format_command_prompt()
        
        # Should contain the prompt marker
        assert ">" in prompt
    
    def test_multiple_format_calls_consistent(self):
        """Test that multiple format calls are consistent"""
        formatter = ChatUIFormatter({"user_message": "white"})
        text = "Test message"
        
        formatted1 = formatter.format_user_message(text)
        formatted2 = formatter.format_user_message(text)
        
        # Should produce consistent output
        assert formatted1 == formatted2
    
    def test_formatter_with_hex_colors(self):
        """Test formatter with hex color config"""
        config = {
            "user_message": "#cccccc",
            "ai_message": "#ffffff"
        }
        formatter = ChatUIFormatter(config)
        
        formatted_user = formatter.format_user_message("User input")
        formatted_ai = formatter.format_ai_message("AI response")
        
        # Both should format successfully
        assert "User input" in formatted_user
        assert "AI response" in formatted_ai


class TestColorMapping:
    """Test color name mappings"""
    
    def test_named_colors_dictionary_exists(self):
        """Test that NAMED_COLORS dictionary exists"""
        assert NAMED_COLORS is not None
        assert isinstance(NAMED_COLORS, dict)
    
    def test_named_colors_has_common_colors(self):
        """Test that NAMED_COLORS includes common colors"""
        expected_colors = ["white", "black", "red", "green", "blue", "yellow", "cyan", "magenta"]
        for color in expected_colors:
            assert color.lower() in {k.lower() for k in NAMED_COLORS.keys()}
    
    def test_named_colors_returns_ansi_codes(self):
        """Test that NAMED_COLORS maps to ANSI codes"""
        for color_name, ansi_code in NAMED_COLORS.items():
            # ANSI codes should be strings
            assert isinstance(ansi_code, str)
            # Should contain escape sequence or be a valid colorama constant
            assert len(ansi_code) > 0


class TestColorEdgeCases:
    """Test edge cases in color handling"""
    
    def test_formatter_with_empty_config(self):
        """Test formatter with empty config uses defaults"""
        formatter = ChatUIFormatter({})
        assert formatter.user_color is not None
        assert formatter.ai_color is not None
    
    def test_parse_color_with_spaces(self):
        """Test parsing color names with spaces"""
        # Should handle or ignore spaces
        color = parse_color(" white ")
        assert color is not None
    
    def test_hex_color_with_or_without_hash(self):
        """Test hex color parsing with or without # prefix"""
        color1 = parse_color("#ffffff")
        color2 = parse_color("ffffff")
        # Both should work or both should have same behavior
        assert color1 is not None
        assert color2 is not None
    
    def test_formatter_multiline_message(self):
        """Test formatting messages with multiple lines"""
        formatter = ChatUIFormatter({})
        multiline = "Line 1\nLine 2\nLine 3"
        formatted = formatter.format_user_message(multiline)
        
        # Should preserve newlines
        assert "Line 1" in formatted
        assert "Line 2" in formatted
        assert "Line 3" in formatted
    
    def test_formatter_message_with_unicode(self):
        """Test formatting messages with unicode characters"""
        formatter = ChatUIFormatter({})
        unicode_msg = "Hello 世界 🌍 Здравствуй"
        formatted = formatter.format_user_message(unicode_msg)
        
        # Unicode should be preserved
        assert "世界" in formatted
        assert "🌍" in formatted
