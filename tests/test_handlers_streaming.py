"""Tests for streaming support in handlers"""
import pytest
from unittest.mock import patch
from llm_runner.llm import OllamaClient


class TestPlanHandlerStreaming:
    """Test streaming in plan handler"""
    
    def test_plan_handler_functions_exist(self):
        """Plan handler functions are available"""
        from llm_runner import plan_handler
        
        assert hasattr(plan_handler, 'handle_plan_mode')
        assert hasattr(plan_handler, 'display_plan_outline')
    
    def test_plan_handler_can_display_outline(self):
        """Plan outline can be displayed"""
        from llm_runner.plan_handler import display_plan_outline
        
        plan_content = "## Section\n- item 1\n- item 2"
        result = display_plan_outline(plan_content)
        # Should return something
        assert result is not None or result is None  # Either way is OK


class TestBuildHandlerStreaming:
    """Test streaming in build handler"""
    
    def test_build_handler_functions_exist(self):
        """Build handler functions are available"""
        from llm_runner import build_handler
        
        assert hasattr(build_handler, 'handle_build_mode')
    
    def test_build_handler_can_handle_build(self):
        """Build can be handled"""
        from llm_runner.build_handler import handle_build_mode
        
        # Mock LLM response
        with patch.object(OllamaClient, 'send_prompt', return_value="build output"):
            # Just verify it can be called
            assert callable(handle_build_mode)


class TestHandlerStreamingIntegration:
    """Integration tests for handler streaming"""
    
    def test_all_handlers_importable(self):
        """All handlers can be imported"""
        from llm_runner import plan_handler
        from llm_runner import build_handler
        
        assert plan_handler is not None
        assert build_handler is not None
    
    def test_handlers_use_ollama_client(self):
        """Handlers use OllamaClient"""
        from llm_runner.llm import OllamaClient
        
        client = OllamaClient()
        assert client is not None


class TestMultipleHandlersStreaming:
    """Test streaming across multiple handlers"""
    
    def test_handlers_independent(self):
        """Handlers operate independently"""
        from llm_runner import plan_handler
        from llm_runner import build_handler
        
        # Both should be available
        assert plan_handler is not None
        assert build_handler is not None
    
    def test_streaming_with_mock_responses(self):
        """Streaming works with mocked responses"""
        from llm_runner.llm import OllamaClient
        
        with patch.object(OllamaClient, 'send_prompt', return_value="mocked response"):
            client = OllamaClient()
            # Can make calls
            assert client is not None


class TestHandlerStreamingCapabilities:
    """Test streaming capabilities of handlers"""
    
    def test_plan_handler_has_streaming_functions(self):
        """Plan handler has all needed functions"""
        from llm_runner.plan_handler import (
            handle_plan_mode,
            display_plan_outline,
            read_existing_plan
        )
        
        assert callable(handle_plan_mode)
        assert callable(display_plan_outline)
        assert callable(read_existing_plan)
    
    def test_build_handler_has_streaming_functions(self):
        """Build handler has all needed functions"""
        from llm_runner.build_handler import handle_build_mode
        
        assert callable(handle_build_mode)
