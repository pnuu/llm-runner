"""Tests for delegate mode handler"""
from unittest.mock import MagicMock, patch
from llm_runner.delegate_handler import handle_delegate_mode


class TestDelegateHandler:
    """Test delegate mode integration"""
    
    def test_delegate_mode_initialization(self):
        """Test delegate mode handler initializes correctly"""
        config = {"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
        
        with patch("llm_runner.delegate_handler.AgentOrchestrator"):
            with patch("llm_runner.delegate_handler.PlanAgent"):
                with patch("builtins.print"):
                    result = handle_delegate_mode(
                        "Build API",
                        config=config,
                        use_context=False
                    )
                    
                    assert result is not None
    
    def test_delegate_mode_with_context(self):
        """Test delegate mode uses AGENTS.md context"""
        config = {"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
        
        with patch("llm_runner.delegate_handler.AgentOrchestrator"):
            with patch("llm_runner.delegate_handler.PlanAgent"):
                with patch("llm_runner.delegate_handler.read_agents_context", return_value="# Project"):
                    with patch("builtins.print"):
                        result = handle_delegate_mode(
                            "Task",
                            config=config,
                            use_context=True
                        )
                        
                        assert result is not None
    
    def test_delegate_creates_initial_agent(self):
        """Test that delegate mode creates initial agent"""
        config = {"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
        
        with patch("llm_runner.delegate_handler.AgentOrchestrator") as mock_orch:
            with patch("llm_runner.delegate_handler.PlanAgent") as mock_agent:
                with patch("builtins.print"):
                    mock_agent_instance = MagicMock()
                    mock_agent.return_value = mock_agent_instance
                    
                    handle_delegate_mode("Task", config=config)
                    
                    mock_agent.assert_called()
    
    def test_delegate_execution_flow(self):
        """Test full delegation execution flow"""
        config = {"model": "mistral:7b", "ollama_url": "http://localhost:11434"}
        
        with patch("llm_runner.delegate_handler.AgentOrchestrator") as mock_orch_class:
            with patch("llm_runner.delegate_handler.PlanAgent") as mock_agent_class:
                with patch("builtins.print"):
                    mock_orch = MagicMock()
                    mock_orch_class.return_value = mock_orch
                    
                    mock_agent = MagicMock()
                    mock_agent.decompose_task.return_value = "Sub-tasks"
                    mock_agent_class.return_value = mock_agent
                    
                    result = handle_delegate_mode(
                        "Complex task",
                        config=config
                    )
                    
                    assert result is not None
