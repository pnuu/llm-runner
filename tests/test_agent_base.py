"""Tests for Agent base class"""
import pytest
from llm_runner.agent import Agent


class TestAgentBase:
    """Test Agent base class initialization and properties"""
    
    def test_agent_creation(self):
        """Test basic agent creation"""
        agent = Agent(
            role="code",
            task="Create a function",
            llm_client=None
        )
        
        assert agent.role == "code"
        assert agent.task == "Create a function"
        assert agent.status == "pending"
        assert isinstance(agent.id, str)
    
    def test_agent_result_store(self):
        """Test result store initialization"""
        agent = Agent(role="test", task="Test", llm_client=None)
        
        assert isinstance(agent.result_store, dict)
        assert len(agent.result_store) == 0
    
    def test_agent_store_result(self):
        """Test storing results"""
        agent = Agent(role="test", task="Test", llm_client=None)
        
        agent.store_result("step1", "result_value")
        
        assert agent.result_store["step1"] == "result_value"
    
    def test_agent_get_result(self):
        """Test retrieving stored results"""
        agent = Agent(role="test", task="Test", llm_client=None)
        agent.store_result("data", {"key": "value"})
        
        result = agent.get_result("data")
        
        assert result == {"key": "value"}
    
    def test_agent_parent_id(self):
        """Test parent-child relationship tracking"""
        parent_agent = Agent(role="parent", task="Parent task", llm_client=None)
        
        child_agent = Agent(
            role="child",
            task="Child task",
            parent_id=parent_agent.id,
            llm_client=None
        )
        
        assert child_agent.parent_id == parent_agent.id
    
    def test_agent_capabilities(self):
        """Test agent capability tracking"""
        capabilities = ["planning", "execution", "testing"]
        agent = Agent(
            role="code",
            task="Build API",
            capabilities=capabilities,
            llm_client=None
        )
        
        assert agent.capabilities == capabilities
    
    def test_agent_status_transitions(self):
        """Test agent status lifecycle"""
        agent = Agent(role="test", task="Test", llm_client=None)
        
        # Initially pending
        assert agent.status == "pending"
        
        # Move to running
        agent.status = "running"
        assert agent.status == "running"
        
        # Complete
        agent.status = "complete"
        assert agent.status == "complete"
