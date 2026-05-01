"""Test LLM integration module"""
import pytest
from unittest.mock import patch, MagicMock
from llm_runner.llm import OllamaClient, check_ollama_connection


def test_ollama_client_init():
    """Test OllamaClient initialization"""
    client = OllamaClient(url="http://localhost:11434")
    assert client.url == "http://localhost:11434"


def test_ollama_client_send_prompt_success():
    """Test sending a prompt to Ollama"""
    client = OllamaClient(url="http://localhost:11434")
    
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Hello, this is a response"
        }
        mock_post.return_value = mock_response
        
        result = client.send_prompt("Hello", model="mistral", temperature=0.7)
        
        assert result == "Hello, this is a response"
        mock_post.assert_called_once()


def test_ollama_client_send_prompt_with_params():
    """Test sending prompt with all parameters"""
    client = OllamaClient(url="http://localhost:11434")
    
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test"}
        mock_post.return_value = mock_response
        
        result = client.send_prompt(
            "test prompt",
            model="mistral",
            temperature=0.5
        )
        
        # Verify the request was made with correct parameters
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "mistral"
        assert call_args[1]["json"]["temperature"] == 0.5


def test_check_ollama_connection_success():
    """Test checking Ollama connection"""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = check_ollama_connection("http://localhost:11434")
        
        assert result is True


def test_check_ollama_connection_failure():
    """Test checking Ollama connection failure"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection failed")
        
        result = check_ollama_connection("http://localhost:11434")
        
        assert result is False


def test_check_ollama_connection_with_timeout():
    """Test connection check respects timeout"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Timeout")
        
        result = check_ollama_connection("http://localhost:11434", timeout=2)
        
        assert result is False


def test_ollama_client_handles_error_response():
    """Test that client handles error responses from API"""
    client = OllamaClient(url="http://localhost:11434")
    
    with patch("requests.post") as mock_post:
        # Simulate API error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "model 'mistral' not found"
        }
        mock_post.return_value = mock_response
        
        result = client.send_prompt("hello", model="mistral")
        
        # Should return empty or error message, not crash
        assert result is not None


def test_get_available_models():
    """Test listing available models from Ollama"""
    from llm_runner.llm import get_available_models
    
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "mistral:7b"},
                {"name": "neural-chat"}
            ]
        }
        mock_get.return_value = mock_response
        
        models = get_available_models("http://localhost:11434")
        
        assert len(models) == 2
        assert "mistral:7b" in models
