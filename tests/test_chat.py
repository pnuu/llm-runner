"""Test interactive chat module"""
from unittest.mock import patch, MagicMock
import pytest
from llm_runner.chat import InteractiveChat, ConversationHistory


def test_conversation_history_init():
    """Test ConversationHistory initialization"""
    history = ConversationHistory()
    assert len(history.messages) == 0


def test_conversation_history_add_message():
    """Test adding messages to history"""
    history = ConversationHistory()
    history.add_user_message("Hello")
    history.add_assistant_message("Hi there!")
    
    assert len(history.messages) == 2
    assert history.messages[0]["role"] == "user"
    assert history.messages[0]["content"] == "Hello"


def test_conversation_history_clear():
    """Test clearing conversation history"""
    history = ConversationHistory()
    history.add_user_message("Hello")
    history.add_assistant_message("Hi!")
    
    history.clear()
    
    assert len(history.messages) == 0


def test_interactive_chat_init():
    """Test InteractiveChat initialization"""
    with patch("llm_runner.chat.OllamaClient"):
        with patch("llm_runner.chat.check_ollama_connection", return_value=True):
            chat = InteractiveChat(
                ollama_url="http://localhost:11434",
                model="mistral",
                temperature=0.7
            )
            assert chat.model == "mistral"
            assert chat.temperature == 0.7


def test_interactive_chat_connection_check():
    """Test that InteractiveChat checks Ollama connection"""
    with patch("llm_runner.chat.check_ollama_connection", return_value=False):
        with pytest.raises(Exception):
            InteractiveChat(
                ollama_url="http://localhost:11434",
                model="mistral"
            )


def test_interactive_chat_process_user_input():
    """Test processing user input commands"""
    with patch("llm_runner.chat.OllamaClient"):
        with patch("llm_runner.chat.check_ollama_connection", return_value=True):
            chat = InteractiveChat()
            
            # Test /clear command
            chat.history.add_user_message("test")
            result = chat.process_input("/clear")
            assert result is None
            assert len(chat.history.messages) == 0


def test_interactive_chat_send_message():
    """Test sending a message to the model"""
    with patch("llm_runner.chat.OllamaClient") as mock_client_class:
        with patch("llm_runner.chat.check_ollama_connection", return_value=True):
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "Response from model"
            mock_client_class.return_value = mock_client
            
            chat = InteractiveChat()
            response = chat.send_message("Hello")
            
            assert response == "Response from model"
            assert len(chat.history.messages) == 2  # user + assistant


def test_interactive_chat_run_quit_command():
    """Test that /quit command exits"""
    with patch("llm_runner.chat.OllamaClient"):
        with patch("llm_runner.chat.check_ollama_connection", return_value=True):
            chat = InteractiveChat()
            
            result = chat.process_input("/quit")
            assert result == "quit"
