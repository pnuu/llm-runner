"""End-to-end integration tests"""
import pytest
from unittest.mock import patch, MagicMock
from llm_runner.config import load_config, save_config
from llm_runner.cli import run_cli
import tempfile
import os


def test_e2e_config_loading():
    """Test full configuration loading workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.yaml")
        
        # Config doesn't exist yet - should create default
        config = load_config(config_file)
        assert os.path.exists(config_file)
        assert config["model"] == "mistral"


def test_e2e_single_prompt_workflow():
    """Test complete single prompt workflow"""
    with patch("llm_runner.llm.requests.post") as mock_post:
        with patch("llm_runner.llm.requests.get") as mock_get:
            # Mock Ollama connection check
            mock_get.return_value = MagicMock(status_code=200)
            
            # Mock prompt response
            mock_post.return_value = MagicMock(
                json=MagicMock(return_value={"response": "Test response"})
            )
            
            # Run CLI in ask mode
            with patch("builtins.print") as mock_print:
                run_cli(["/ask", "hello"])
                
                # Should print the response
                mock_print.assert_called()


def test_e2e_interactive_mode_startup():
    """Test interactive mode startup and connection"""
    with patch("llm_runner.llm.requests.get") as mock_get:
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            # Mock Ollama connection
            mock_get.return_value = MagicMock(status_code=200)
            
            # Should start without errors and handle KeyboardInterrupt
            with patch("builtins.print"):
                run_cli([])


def test_e2e_model_override():
    """Test model can be overridden via CLI"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.yaml")
        config = load_config(config_file)
        assert config["model"] == "mistral"
        
        # Now override should work
        with patch("llm_runner.llm.requests.post") as mock_post:
            with patch("llm_runner.llm.requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                mock_post.return_value = MagicMock(
                    json=MagicMock(return_value={"response": "response"})
                )
                
                with patch("builtins.print"):
                    run_cli(["/ask", "test", "--model", "neural-chat", "--config", config_file])
                
                # Verify the override was used
                call_args = mock_post.call_args
                assert call_args[1]["json"]["model"] == "neural-chat"


def test_e2e_cli_callable():
    """Test that llm-runner command is callable"""
    # This verifies the entrypoint was configured correctly
    import llm_runner.__main__
    assert hasattr(llm_runner.__main__, 'main')
    assert callable(llm_runner.__main__.main)
