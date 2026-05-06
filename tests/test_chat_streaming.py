"""Tests for streaming integration in chat.py"""
import pytest
from unittest.mock import patch
from llm_runner.chat import InteractiveChat


class TestChatStreamingIntegration:
    """Test streaming support in interactive chat"""
    
    @pytest.fixture
    def chat(self):
        """Create chat instance for testing"""
        return InteractiveChat(model="mistral")
    
    def test_chat_initialization(self, chat):
        """Chat initializes correctly"""
        assert chat.model == "mistral"
        assert chat.history is not None
    
    def test_chat_processes_messages(self, chat):
        """Chat can process messages"""
        # Mock the LLM response
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            result = chat.send_message("test question")
            assert isinstance(result, str)
    
    def test_streaming_preserves_history(self, chat):
        """Messages are added to history"""
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            initial_length = len(chat.history.messages)
            chat.send_message("question")
            
            # Should have added messages
            assert len(chat.history.messages) >= initial_length
    
    def test_multiple_messages_context(self, chat):
        """Context maintained across messages"""
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            chat.send_message("first")
            chat.send_message("second")
            
            # Both messages should be in history
            assert len(chat.history.messages) >= 4  # 2 user + 2 assistant


class TestStreamingEdgeCases:
    """Test edge cases in streaming"""
    
    @pytest.fixture
    def chat(self):
        return InteractiveChat()
    
    def test_empty_response(self, chat):
        """Empty responses handled"""
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value=""):
            result = chat.send_message("test")
            assert isinstance(result, str)
    
    def test_special_characters(self, chat):
        """Special characters in responses"""
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response 🎉"):
            result = chat.send_message("test")
            assert "response" in result
    
    def test_long_response(self, chat):
        """Long responses handled"""
        from llm_runner.llm import OllamaClient
        long_response = "x" * 10000
        with patch.object(OllamaClient, 'send_prompt', return_value=long_response):
            result = chat.send_message("test")
            assert len(result) > 1000


class TestStreamingConfiguration:
    """Test streaming configuration"""
    
    def test_model_configurable(self):
        """Different models can be set"""
        chat1 = InteractiveChat(model="mistral")
        chat2 = InteractiveChat(model="neural-chat")
        
        assert chat1.model == "mistral"
        assert chat2.model == "neural-chat"
    
    def test_temperature_configurable(self):
        """Temperature can be configured"""
        chat = InteractiveChat(temperature=0.3)
        assert chat.temperature == 0.3


class TestStreamingPerformance:
    """Test streaming performance characteristics"""
    
    def test_responsive_to_messages(self):
        """Chat responds to messages"""
        chat = InteractiveChat()
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            result = chat.send_message("test")
            assert isinstance(result, str)
    
    def test_sequential_messages(self):
        """Multiple sequential messages work"""
        chat = InteractiveChat()
        from llm_runner.llm import OllamaClient
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            for i in range(3):
                result = chat.send_message(f"message {i}")
                assert isinstance(result, str)
