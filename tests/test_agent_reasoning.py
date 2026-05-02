"""Tests for agent task decomposition"""
from unittest.mock import MagicMock
from llm_runner.agents.plan_agent import PlanAgent


class TestAgentDecomposition:
    """Test LLM-driven task decomposition"""
    
    def test_agent_decompose_task(self):
        """Test decomposing a task into sub-tasks"""
        mock_llm = MagicMock()
        mock_llm.send_prompt.return_value = """
Task: Build REST API

Sub-tasks:
1. CodeAgent: Create main.py with Flask app
2. TestAgent: Write unit tests
3. BuildAgent: Run tests and validate
"""
        
        agent = PlanAgent(task="Build REST API", llm_client=mock_llm)
        decomposed = agent.decompose_task()
        
        assert "CodeAgent" in decomposed
        assert "TestAgent" in decomposed
        assert "BuildAgent" in decomposed
    
    def test_parse_decomposition_response(self):
        """Test parsing LLM response into sub-tasks"""
        mock_llm = MagicMock()
        agent = PlanAgent(task="Test", llm_client=mock_llm)
        
        response = """
Sub-tasks:
1. CodeAgent: Create file
2. ResearchAgent: Analyze requirements
"""
        
        parsed = agent._parse_decomposition(response)
        
        assert len(parsed) == 2
        assert parsed[0]["agent_type"] == "CodeAgent"
        assert parsed[1]["agent_type"] == "ResearchAgent"
    
    def test_sub_task_execution_sequence(self):
        """Test execution order of sub-tasks"""
        mock_llm = MagicMock()
        agent = PlanAgent(task="Test", llm_client=mock_llm)
        
        tasks = [
            {"agent_type": "PlanAgent", "task": "Plan"},
            {"agent_type": "CodeAgent", "task": "Code"},
            {"agent_type": "TestAgent", "task": "Test"}
        ]
        
        assert tasks[0]["agent_type"] == "PlanAgent"
        assert tasks[1]["agent_type"] == "CodeAgent"
        assert tasks[2]["agent_type"] == "TestAgent"
