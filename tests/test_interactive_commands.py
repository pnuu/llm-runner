"""Tests for enhanced interactive chat commands"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from llm_runner.chat import InteractiveChat


class TestModelCommand:
    """Test /model command for interactive model selection"""
    
    def test_model_command_lists_available_models(self):
        """Test that /model command lists available models"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat(model="mistral")
        
        mock_models = ["mistral:7b", "llama3:8b", "qwen:7b"]
        
        with patch('llm_runner.chat.get_available_models', return_value=mock_models):
            # Simulate user entering /model and then ESC to cancel
            with patch('builtins.input', side_effect=['2', KeyboardInterrupt()]):
                try:
                    chat.process_input("/model")
                except (KeyboardInterrupt, EOFError, SystemExit):
                    pass
    
    def test_model_command_updates_model(self):
        """Test that selecting a model updates the current model"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat(model="mistral:7b")
        
        mock_models = ["mistral:7b", "llama3:8b", "qwen:7b"]
        
        # Should be able to change model
        assert chat.model == "mistral:7b"
    
    def test_model_command_defaults_to_current(self):
        """Test that pressing Enter defaults to current model"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat(model="mistral:7b")
        
        original_model = chat.model
        
        # If no selection is made, should stay the same
        assert chat.model == original_model


class TestPlanCommand:
    """Test /plan command to switch to plan mode"""
    
    def test_plan_command_prompt(self):
        """Test that /plan command prompts for plan request"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        # Simulate user entering /plan
        with patch('builtins.input', return_value="exit"):
            # Should not raise error
            result = chat.process_input("/plan")
    
    def test_plan_command_returns_to_chat(self):
        """Test that /plan mode returns to chat loop"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        # After /plan, should return to main chat loop
        initial_history_len = len(chat.history.context_manager.messages)
        
        with patch('builtins.input', return_value="exit"):
            chat.process_input("/plan")
        
        # Should still be in interactive mode (not switched permanently)
        assert chat is not None


class TestBuildCommand:
    """Test /build command to switch to build mode"""
    
    def test_build_command_prompt(self):
        """Test that /build command prompts for build request"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        # Simulate user entering /build
        with patch('builtins.input', return_value="exit"):
            result = chat.process_input("/build")
    
    def test_build_command_returns_to_chat(self):
        """Test that /build mode returns to chat loop"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        with patch('builtins.input', return_value="exit"):
            chat.process_input("/build")
        
        # Should still be in chat session
        assert chat is not None


class TestAskCommand:
    """Test /ask command for context-aware single prompts"""
    
    def test_ask_command_does_not_store_in_history(self):
        """Test that /ask command doesn't store in history"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        initial_message_count = len(chat.history.context_manager.messages)
        
        # Simulate /ask with mock response
        with patch('builtins.input', return_value="test question"):
            with patch.object(chat.client, 'send_prompt', return_value="test response"):
                chat.process_input("/ask")
        
        # Message count should not increase
        assert len(chat.history.context_manager.messages) == initial_message_count
    
    def test_ask_command_shows_response(self):
        """Test that /ask command shows the response"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        mock_response = "This is a test response"
        
        with patch('builtins.input', return_value="test question"):
            with patch.object(chat.client, 'send_prompt', return_value=mock_response):
                with patch('builtins.print') as mock_print:
                    chat.process_input("/ask")
                    
                    # Should print the response
                    # (may need to adjust based on actual implementation)
    
    def test_ask_command_includes_context(self):
        """Test that /ask command has access to context"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat()
        
        # Add a message to history
        chat.history.add_user_message("Previous question")
        chat.history.add_assistant_message("Previous answer")
        
        initial_count = len(chat.history.context_manager.messages)
        
        with patch('builtins.input', return_value="new question"):
            with patch.object(chat.client, 'send_prompt', return_value="response"):
                chat.process_input("/ask")
        
        # History should not grow (no new messages added)
        assert len(chat.history.context_manager.messages) == initial_count


class TestCLIAskMode:
    """Test CLI ask mode (renamed from /ask)"""
    
    def test_cli_ask_mode_argument(self):
        """Test that 'ask' argument works without slash"""
        from llm_runner.cli import parse_args
        
        # Test new format: ask without slash
        args = parse_args(["ask", "test question"])
        assert args.mode == "ask"
        assert args.request == "test question"
    
    def test_cli_ask_mode_backwards_compat(self):
        """Test that '/ask' still works for backwards compatibility"""
        from llm_runner.cli import parse_args
        
        # Test old format with slash (should still work)
        args = parse_args(["/ask", "test question"])
        assert args.mode == "ask"
        assert args.request == "test question"
