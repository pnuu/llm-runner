"""Tests for dynamic context length retrieval from models"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_runner.llm import OllamaClient


class TestModelContextLength:
    """Test getting context length from Ollama models"""
    
    def test_get_context_length_llama_model(self):
        """Test extracting context length from llama model info"""
        client = OllamaClient()
        
        mock_response = {
            "model_info": {
                "llama.context_length": 32768,
                "llama.embedding_length": 4096,
            }
        }
        
        with patch.object(client, 'send_prompt') as mock_send:
            # Mock the API call that gets model info
            with patch('requests.post') as mock_post:
                mock_post.return_value.json.return_value = mock_response
                
                context_length = client.get_model_context_length("mistral:7b")
                
                assert context_length == 32768
    
    def test_get_context_length_fallback_to_default(self):
        """Test fallback to 4096 when context_length field not found"""
        client = OllamaClient()
        
        mock_response = {
            "model_info": {
                "llama.embedding_length": 4096,
                # Missing llama.context_length
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            
            context_length = client.get_model_context_length("mistral:7b")
            
            assert context_length == 4096
    
    def test_get_context_length_fallback_on_error(self):
        """Test fallback when API call fails"""
        client = OllamaClient()
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            context_length = client.get_model_context_length("mistral:7b")
            
            assert context_length == 4096
    
    def test_get_context_length_api_endpoint(self):
        """Test correct API endpoint is called"""
        client = OllamaClient(url="http://localhost:11434")
        
        mock_response = {
            "model_info": {
                "llama.context_length": 16384,
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            
            context_length = client.get_model_context_length("llama3:8b")
            
            # Verify correct endpoint was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "11434/api/show" in call_args[0][0]
            assert call_args[1]["json"]["name"] == "llama3:8b"
    
    def test_get_context_length_with_different_models(self):
        """Test context length varies by model"""
        client = OllamaClient()
        
        test_cases = [
            ("mistral:7b", 32768),
            ("llama3:8b", 8192),
            ("qwen:7b", 32768),
            ("phi:latest", 2048),
        ]
        
        for model_name, expected_length in test_cases:
            mock_response = {
                "model_info": {
                    "llama.context_length": expected_length,
                }
            }
            
            with patch('requests.post') as mock_post:
                mock_post.return_value.json.return_value = mock_response
                
                context_length = client.get_model_context_length(model_name)
                
                assert context_length == expected_length
    
    def test_get_context_length_caching(self):
        """Test that context lengths are cached to avoid repeated API calls"""
        client = OllamaClient()
        
        mock_response = {
            "model_info": {
                "llama.context_length": 32768,
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            
            # Call twice for same model
            length1 = client.get_model_context_length("mistral:7b")
            length2 = client.get_model_context_length("mistral:7b")
            
            assert length1 == length2 == 32768
            # Should only call API once due to caching
            assert mock_post.call_count == 1


class TestInteractiveChatContextUsage:
    """Test that InteractiveChat uses dynamic context"""
    
    def test_interactive_chat_respects_max_context_tokens(self):
        """Verify InteractiveChat uses passed max_context_tokens"""
        from llm_runner.chat import InteractiveChat
        
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            chat = InteractiveChat(max_context_tokens=16384)
            
            # Verify ContextManager received the correct value
            assert chat.history.context_manager.max_tokens == 16384
    
    def test_conversation_history_max_tokens_passthrough(self):
        """Verify ConversationHistory passes max_tokens to ContextManager"""
        from llm_runner.chat import ConversationHistory
        
        custom_max = 8192
        history = ConversationHistory(max_tokens=custom_max)
        
        assert history.context_manager.max_tokens == custom_max
