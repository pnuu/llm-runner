"""Test AGENTS.md integration with plan/build modes"""
import os
import tempfile
from unittest.mock import patch, MagicMock
from llm_runner.plan_handler import read_agents_context, handle_plan_mode
from llm_runner.build_handler import handle_build_mode


def test_read_agents_md_when_exists():
    """Test reading AGENTS.md when it exists"""
    with tempfile.TemporaryDirectory() as tmpdir:
        agents_file = os.path.join(tmpdir, "AGENTS.md")
        with open(agents_file, "w") as f:
            f.write("# Build Instructions\nUse TDD")
        
        content = read_agents_context(tmpdir)
        
        assert "Build Instructions" in content
        assert "TDD" in content


def test_read_agents_md_when_missing():
    """Test reading AGENTS.md when it doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = read_agents_context(tmpdir)
        
        # Should return empty string, not error
        assert content == ""


def test_plan_mode_with_agents_context():
    """Test plan mode uses AGENTS.md as context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AGENTS.md
        agents_file = os.path.join(tmpdir, "AGENTS.md")
        with open(agents_file, "w") as f:
            f.write("# Project Guidelines\nUse Python 3.8+\nWrite tests first")
        
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            with patch("llm_runner.plan_handler.PlanWriter"):
                mock_gen = MagicMock()
                mock_plan = MagicMock()
                mock_gen.generate_plan.return_value = mock_plan
                mock_gen_class.return_value = mock_gen
                
                with patch("builtins.print"):
                    handle_plan_mode(
                        "Create API",
                        output_dir=tmpdir,
                        config={"model": "mistral:7b", "ollama_url": "http://localhost:11434"},
                        use_context=True
                    )
                
                # Verify context was passed to generate_plan
                call_args = mock_gen.generate_plan.call_args
                # Context should be in either positional or keyword args
                assert "context" in call_args[1] or (len(call_args[0]) > 1 and call_args[0][1])


def test_build_mode_with_agents_context():
    """Test build mode uses AGENTS.md as context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AGENTS.md
        agents_file = os.path.join(tmpdir, "AGENTS.md")
        with open(agents_file, "w") as f:
            f.write("# Project Configuration\nFramework: Django\nVersion: 4.0")
        
        with patch("llm_runner.build_handler.BuildExecutor"):
            with patch("llm_runner.build_handler.OllamaClient") as mock_client_class:
                with patch("llm_runner.build_handler.check_ollama_connection", return_value=True):
                    mock_client = MagicMock()
                    mock_client.send_prompt.return_value = "Plan created"
                    mock_client_class.return_value = mock_client
                    
                    with patch("builtins.print"):
                        handle_build_mode(
                            "Build authentication",
                            workspace_dir=tmpdir,
                            config={"model": "mistral:7b", "ollama_url": "http://localhost:11434"},
                            use_context=True
                        )
                    
                    # Verify context was included in prompt
                    call_args = mock_client.send_prompt.call_args
                    prompt = call_args[0][0]
                    # The prompt should contain the context
                    assert "Framework" in prompt or "Django" in prompt


def test_plan_mode_without_context_flag():
    """Test plan mode doesn't use context when flag is False"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AGENTS.md
        with open(os.path.join(tmpdir, "AGENTS.md"), "w") as f:
            f.write("# Secret Instructions\nNot used")
        
        with patch("llm_runner.plan_handler.PlanGenerator") as mock_gen_class:
            with patch("llm_runner.plan_handler.PlanWriter"):
                mock_gen = MagicMock()
                mock_plan = MagicMock()
                mock_gen.generate_plan.return_value = mock_plan
                mock_gen_class.return_value = mock_gen
                
                with patch("builtins.print"):
                    handle_plan_mode(
                        "Request",
                        output_dir=tmpdir,
                        config={"model": "mistral:7b", "ollama_url": "http://localhost:11434"},
                        use_context=False
                    )
                
                # Context should be None or empty
                call_args = mock_gen.generate_plan.call_args
                context = call_args[1].get("context")
                assert context is None or context == ""


def test_cli_context_flag():
    """Test that --context flag is properly parsed"""
    from llm_runner.cli import parse_args
    
    args = parse_args(["plan", "Request", "--context"])
    assert args.context is True
    
    args_no_context = parse_args(["plan", "Request"])
    assert not hasattr(args_no_context, "context") or not args_no_context.context
