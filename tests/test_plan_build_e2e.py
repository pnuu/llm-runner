"""End-to-end tests for plan and build modes"""
import os
import tempfile
from unittest.mock import patch, MagicMock
from llm_runner.cli import run_cli


def test_e2e_plan_mode_workflow():
    """Test complete plan mode workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        with patch("llm_runner.llm.requests.post") as mock_post:
            with patch("llm_runner.llm.requests.get") as mock_get:
                # Mock Ollama connection and response
                mock_get.return_value = MagicMock(status_code=200)
                mock_post.return_value = MagicMock(
                    json=MagicMock(return_value={
                        "response": """Title: Test API
Approach: Create REST endpoints
Steps:
- Define routes
- Add handlers
Notes: Simple implementation"""
                    })
                )
                
                # Run plan mode
                with patch("builtins.print"):
                    run_cli(["plan", "Create REST API"])
                
                # Verify plan.md was created
                assert os.path.exists("plan.md")
                
                with open("plan.md", "r") as f:
                    content = f.read()
                    assert "Test API" in content
                    assert "REST endpoints" in content


def test_e2e_build_mode_workflow():
    """Test complete build mode workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        with patch("llm_runner.llm.requests.post") as mock_post:
            with patch("llm_runner.llm.requests.get") as mock_get:
                # Mock Ollama
                mock_get.return_value = MagicMock(status_code=200)
                mock_post.return_value = MagicMock(
                    json=MagicMock(return_value={
                        "response": "Build plan: Create files and run tests"
                    })
                )
                
                # Run build mode
                with patch("builtins.print"):
                    run_cli(["build", "Add user authentication"])
                
                # Should execute without error
                assert True


def test_e2e_plan_with_context():
    """Test plan mode using AGENTS.md context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create AGENTS.md
        with open("AGENTS.md", "w") as f:
            f.write("# Use TDD\nWrite tests first")
        
        with patch("llm_runner.llm.requests.post") as mock_post:
            with patch("llm_runner.llm.requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                mock_post.return_value = MagicMock(
                    json=MagicMock(return_value={
                        "response": "Title: API\nApproach: TDD\nSteps:\n- Test\nNotes: Good"
                    })
                )
                
                with patch("builtins.print"):
                    run_cli(["plan", "Build API", "--context"])
                
                # Should use context
                assert os.path.exists("plan.md")


def test_e2e_plan_mode_with_model_override():
    """Test plan mode with model override"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        with patch("llm_runner.llm.requests.post") as mock_post:
            with patch("llm_runner.llm.requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                mock_post.return_value = MagicMock(
                    json=MagicMock(return_value={
                        "response": "Title: Plan\nApproach: Test\nSteps:\n- Test\nNotes: None"
                    })
                )
                
                with patch("builtins.print"):
                    run_cli(["plan", "Request", "--model", "neural-chat"])
                
                # Verify model was used
                call_args = mock_post.call_args
                assert call_args[1]["json"]["model"] == "neural-chat"


def test_e2e_error_handling_no_connection():
    """Test error handling when Ollama is not available"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        with patch("llm_runner.llm.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            # Should handle error gracefully
            with patch("builtins.print"):
                run_cli(["plan", "Request"])
            
            # Should not crash


def test_e2e_executor_creates_files():
    """Test that build mode executor actually creates files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Directly test executor
        from llm_runner.executor import BuildExecutor
        
        executor = BuildExecutor(workspace_dir=tmpdir)
        
        # Create a file through executor
        result = executor.execute_tool("create_file", ["test.py", "print('hello')"])
        
        # Verify file was created
        assert os.path.exists(os.path.join(tmpdir, "test.py"))
        assert "created" in result.lower()


def test_e2e_executor_runs_commands():
    """Test that executor can run shell commands"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        from llm_runner.executor import BuildExecutor
        
        executor = BuildExecutor(workspace_dir=tmpdir)
        
        # Run a command
        result = executor.execute_tool("run_command", ["echo 'test output'"])
        
        assert "test output" in result
