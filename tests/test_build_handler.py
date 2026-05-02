"""Test build mode handler"""
import tempfile
from unittest.mock import patch, MagicMock
from llm_runner.build_handler import handle_build_mode


def test_handle_build_mode_success():
    """Test successful build mode execution"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.build_handler.BuildExecutor") as mock_executor_class:
            with patch("llm_runner.build_handler.OllamaClient") as mock_client_class:
                with patch("llm_runner.build_handler.check_ollama_connection", return_value=True):
                    mock_executor = MagicMock()
                    mock_executor_class.return_value = mock_executor
                    
                    mock_client = MagicMock()
                    mock_client.send_prompt.return_value = "Plan generated"
                    mock_client_class.return_value = mock_client
                    
                    result = handle_build_mode(
                        "Create a Python script",
                        workspace_dir=tmpdir,
                        config={"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
                    )
                    
                    # Should have used executor
                    mock_executor_class.assert_called_once()


def test_handle_build_mode_with_context():
    """Test build mode with AGENTS.md context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.build_handler.BuildExecutor"):
            with patch("llm_runner.build_handler.OllamaClient") as mock_client_class:
                with patch("llm_runner.build_handler.check_ollama_connection", return_value=True):
                    with patch("llm_runner.build_handler.read_agents_context") as mock_read:
                        mock_read.return_value = "Use TDD"
                        mock_client = MagicMock()
                        mock_client.send_prompt.return_value = "Output"
                        mock_client_class.return_value = mock_client
                        
                        handle_build_mode("Request", workspace_dir=tmpdir, use_context=True)
                        
                        # Should include context
                        mock_read.assert_called_once()


def test_handle_build_mode_error_handling():
    """Test error handling in build mode"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.build_handler.check_ollama_connection", return_value=False):
            result = handle_build_mode("Request", workspace_dir=tmpdir)
            
            # Should handle connection error gracefully
            assert result is None or "error" in str(result).lower()


def test_handle_build_mode_uses_config():
    """Test that build mode uses provided config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.build_handler.OllamaClient") as mock_client_class:
            with patch("llm_runner.build_handler.check_ollama_connection", return_value=True):
                with patch("llm_runner.build_handler.BuildExecutor"):
                    mock_client = MagicMock()
                    mock_client.send_prompt.return_value = "Done"
                    mock_client_class.return_value = mock_client
                    
                    config = {
                        "model": "neural-chat",
                        "ollama_url": "http://custom:9999"
                    }
                    
                    handle_build_mode("Request", workspace_dir=tmpdir, config=config)
                    
                    # Should use config
                    call_args = mock_client_class.call_args
                    assert call_args[1].get("url") == "http://custom:9999"
