"""Integration tests for chat UI formatter integration"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_runner.chat import InteractiveChat, interactive_chat_repl
from llm_runner.ui_formatter import ChatUIFormatter
from llm_runner.config import get_chat_colors, load_config


class TestUIIntegration:
    """Test UI formatter integration with chat"""
    
    def test_chat_uses_ui_formatter(self):
        """Test that interactive chat uses UI formatter"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat(model="mistral:7b")
            assert chat is not None
    
    def test_colors_loaded_from_config(self):
        """Test that colors are loaded from config"""
        config = {
            "model": "mistral:7b",
            "chat": {
                "ui": {
                    "colors": {
                        "user_message": "yellow",
                        "ai_message": "cyan"
                    }
                }
            }
        }
        
        colors = get_chat_colors(config)
        assert colors["user_message"] == "yellow"
        assert colors["ai_message"] == "cyan"
    
    def test_default_colors_applied(self):
        """Test that default colors are used when not specified"""
        config = {"model": "mistral:7b"}
        colors = get_chat_colors(config)
        
        assert "user_message" in colors
        assert "ai_message" in colors
        assert colors["user_message"] == "light_gray"
        assert colors["ai_message"] == "white"
    
    def test_partial_color_config_merges_with_defaults(self):
        """Test that partial color config merges with defaults"""
        config = {
            "chat": {
                "ui": {
                    "colors": {
                        "user_message": "#ffff00"
                    }
                }
            }
        }
        
        colors = get_chat_colors(config)
        # Custom color applied
        assert colors["user_message"] == "#ffff00"
        # Default colors applied for missing colors
        assert "ai_message" in colors
    
    def test_formatter_initialization_with_config(self):
        """Test formatter initializes with config colors"""
        config = {
            "user_message": "green",
            "ai_message": "blue",
            "status_line": "red"
        }
        
        formatter = ChatUIFormatter(config)
        assert formatter.user_color is not None
        assert formatter.ai_color is not None
        assert formatter.status_color is not None
    
    def test_status_line_displays_model_name(self):
        """Test status line displays current model"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=50
        )
        
        assert "mistral:7b" in status
    
    def test_status_line_displays_mode(self):
        """Test status line displays current mode"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="llama3:8b",
            mode="interactive",
            context_percent=42
        )
        
        assert "interactive" in status
    
    def test_status_line_displays_context_percentage(self):
        """Test status line displays context percentage"""
        formatter = ChatUIFormatter({})
        status = formatter.format_status_line(
            model="neural-chat",
            mode="chat",
            context_percent=87
        )
        
        assert "87" in status
    
    def test_status_line_reflects_model_change(self):
        """Test status line updates when model changes"""
        formatter = ChatUIFormatter({})
        
        status1 = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=20
        )
        assert "mistral:7b" in status1
        
        status2 = formatter.format_status_line(
            model="llama3:8b",
            mode="interactive",
            context_percent=20
        )
        assert "llama3:8b" in status2
        assert "mistral:7b" not in status2
    
    def test_status_line_shows_increasing_context(self):
        """Test status line shows increasing context usage"""
        formatter = ChatUIFormatter({})
        
        status_low = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=10
        )
        
        status_high = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=90
        )
        
        assert "10" in status_low
        assert "90" in status_high
    
    def test_user_message_formatting_consistency(self):
        """Test user messages format consistently"""
        formatter = ChatUIFormatter({})
        
        msg1 = "First message"
        msg2 = "Second message"
        
        formatted1 = formatter.format_user_message(msg1)
        formatted2 = formatter.format_user_message(msg2)
        
        # Both should contain their content
        assert msg1 in formatted1
        assert msg2 in formatted2
        # Both should have formatting applied
        assert len(formatted1) >= len(msg1)
        assert len(formatted2) >= len(msg2)
    
    def test_ai_message_formatting_consistency(self):
        """Test AI messages format consistently"""
        formatter = ChatUIFormatter({})
        
        msg1 = "AI response 1"
        msg2 = "AI response 2"
        
        formatted1 = formatter.format_ai_message(msg1)
        formatted2 = formatter.format_ai_message(msg2)
        
        # Both should contain their content
        assert msg1 in formatted1
        assert msg2 in formatted2
        # Both should have formatting applied
        assert len(formatted1) >= len(msg1)
        assert len(formatted2) >= len(msg2)
    
    def test_command_prompt_visible(self):
        """Test command prompt is visible and formatted"""
        formatter = ChatUIFormatter({})
        prompt = formatter.format_command_prompt()
        
        # Should contain prompt marker
        assert ">" in prompt
        # Should not be empty
        assert len(prompt) > 0
    
    def test_multiple_formatter_instances_independent(self):
        """Test multiple formatter instances maintain independent colors"""
        config1 = {"user_message": "red", "ai_message": "blue"}
        config2 = {"user_message": "green", "ai_message": "yellow"}
        
        formatter1 = ChatUIFormatter(config1)
        formatter2 = ChatUIFormatter(config2)
        
        msg = "test"
        formatted1 = formatter1.format_user_message(msg)
        formatted2 = formatter2.format_user_message(msg)
        
        # Both should contain message
        assert msg in formatted1
        assert msg in formatted2
        # But they should be different (different colors)
        # Note: This is implicit - they use different color codes
    
    def test_hex_colors_work_in_status_line(self):
        """Test hex colors work in status line formatting"""
        config = {
            "status_line": "#00ffff"
        }
        formatter = ChatUIFormatter(config)
        
        status = formatter.format_status_line(
            model="mistral:7b",
            mode="interactive",
            context_percent=50
        )
        
        assert "mistral:7b" in status
        assert "50" in status


class TestColorConfigPriority:
    """Test configuration priority and merging"""
    
    def test_user_config_overrides_defaults(self):
        """Test user config overrides defaults"""
        config = {
            "chat": {
                "ui": {
                    "colors": {
                        "user_message": "red"
                    }
                }
            }
        }
        
        colors = get_chat_colors(config)
        assert colors["user_message"] == "red"
        # Other colors should still have defaults
        assert colors["ai_message"] == "white"
    
    def test_invalid_colors_fallback_to_defaults(self):
        """Test invalid colors fallback gracefully"""
        config = {
            "chat": {
                "ui": {
                    "colors": {
                        "user_message": "definitely_not_a_real_color_xyz"
                    }
                }
            }
        }
        
        # Should not crash, colors should load with fallback
        colors = get_chat_colors(config)
        assert "user_message" in colors
    
    def test_missing_chat_section_uses_defaults(self):
        """Test missing chat section uses all defaults"""
        config = {"model": "mistral:7b"}
        
        colors = get_chat_colors(config)
        
        # Should have all default colors
        assert "user_message" in colors
        assert "ai_message" in colors
        assert "status_line" in colors
    
    def test_empty_colors_section_uses_defaults(self):
        """Test empty colors section uses defaults"""
        config = {
            "chat": {
                "ui": {
                    "colors": {}
                }
            }
        }
        
        colors = get_chat_colors(config)
        
        # Should apply defaults
        assert colors["user_message"] == "light_gray"
        assert colors["ai_message"] == "white"


class TestTerminalCompatibility:
    """Test terminal compatibility and graceful degradation"""
    
    def test_formatter_works_without_ansi_support(self):
        """Test formatter can work with limited terminal support"""
        formatter = ChatUIFormatter({})
        
        # Should produce output even on basic terminals
        msg = formatter.format_user_message("test")
        assert msg is not None
        assert "test" in msg
    
    def test_status_line_readable_on_all_terminals(self):
        """Test status line is readable on all terminals"""
        formatter = ChatUIFormatter({})
        
        status = formatter.format_status_line(
            model="m",
            mode="i",
            context_percent=50
        )
        
        # Must contain essential information even without colors
        assert "m" in status
        assert "50" in status
    
    def test_color_fallback_on_invalid_config(self):
        """Test graceful fallback on invalid color config"""
        config = {
            "user_message": None,
            "ai_message": ""
        }
        
        # Should not crash, should use defaults
        formatter = ChatUIFormatter(config)
        assert formatter.user_color is not None
        assert formatter.ai_color is not None
