"""Test plan mode handler"""
import tempfile
from unittest.mock import patch, MagicMock
from llm_runner.plan_handler import handle_plan_mode


def test_handle_plan_mode_success():
    """Test successful plan mode execution"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            mock_gen = MagicMock()
            mock_plan = MagicMock()
            mock_plan.to_markdown.return_value = "# Test Plan"
            mock_gen.generate_plan.return_value = mock_plan
            mock_gen_class.return_value = mock_gen
            
            with patch("llm_runner.plan_handler.PlanWriter") as mock_writer_class:
                mock_writer = MagicMock()
                mock_writer_class.return_value = mock_writer
                
                result = handle_plan_mode(
                    "Create API",
                    output_dir=tmpdir,
                    config={"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
                )
                
                # Should have called generator and writer
                mock_gen.generate_plan.assert_called_once()
                mock_writer.write_plan.assert_called_once()


def test_handle_plan_mode_with_context():
    """Test plan mode with AGENTS.md context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            with patch("llm_runner.plan_handler.PlanWriter"):
                with patch("llm_runner.plan_handler.read_agents_context") as mock_read:
                    mock_read.return_value = "Use TDD"
                    mock_gen = MagicMock()
                    mock_plan = MagicMock()
                    mock_gen.generate_plan.return_value = mock_plan
                    mock_gen_class.return_value = mock_gen
                    
                    handle_plan_mode("Request", output_dir=tmpdir, use_context=True)
                    
                    # Should pass context to generate_plan
                    call_args = mock_gen.generate_plan.call_args
                    assert "context" in call_args[1] or len(call_args[0]) > 1


def test_handle_plan_mode_error_handling():
    """Test error handling in plan mode"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            mock_gen_class.side_effect = Exception("Connection failed")
            
            result = handle_plan_mode("Request", output_dir=tmpdir)
            
            # Should return False or None indicating failure
            assert result is None or result is False or "error" in str(result).lower()


def test_handle_plan_mode_uses_config():
    """Test that plan mode uses provided config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            with patch("llm_runner.plan_handler.PlanWriter"):
                mock_gen = MagicMock()
                mock_plan = MagicMock()
                mock_gen.generate_plan.return_value = mock_plan
                mock_gen_class.return_value = mock_gen
                
                config = {
                    "model": "neural-chat",
                    "ollama_url": "http://custom:9999"
                }
                
                handle_plan_mode("Request", output_dir=tmpdir, config=config)
                
                # Should initialize generator with config values
                call_args = mock_gen_class.call_args
                assert call_args[1].get("model") == "neural-chat"
                assert call_args[1].get("ollama_url") == "http://custom:9999"
