"""Tests for AgentManager"""
import pytest
from llm_runner.agent_manager import AgentManager
from llm_runner.agent import Agent


class TestAgentManager:
    """Test agent lifecycle management"""
    
    def test_agent_manager_creation(self):
        """Test AgentManager initialization"""
        manager = AgentManager()
        
        assert isinstance(manager.agents, dict)
        assert len(manager.agents) == 0
    
    def test_register_agent(self):
        """Test registering an agent"""
        manager = AgentManager()
        agent = Agent(role="test", task="Test task", llm_client=None)
        
        manager.register_agent(agent)
        
        assert agent.id in manager.agents
        assert manager.agents[agent.id] == agent
    
    def test_spawn_agent(self):
        """Test spawning a new agent"""
        manager = AgentManager()
        
        agent = manager.spawn_agent(
            role="code",
            task="Create function",
            parent_id=None
        )
        
        assert agent.id in manager.agents
        assert agent.role == "code"
        assert agent.task == "Create function"
    
    def test_get_agent(self):
        """Test retrieving an agent"""
        manager = AgentManager()
        agent = manager.spawn_agent("test", "Task")
        
        retrieved = manager.get_agent(agent.id)
        
        assert retrieved == agent
    
    def test_get_nonexistent_agent(self):
        """Test getting non-existent agent returns None"""
        manager = AgentManager()
        
        agent = manager.get_agent("nonexistent")
        
        assert agent is None
    
    def test_track_parent_child_relationship(self):
        """Test tracking parent-child relationships"""
        manager = AgentManager()
        parent = manager.spawn_agent("parent", "Parent task")
        child = manager.spawn_agent("child", "Child task", parent_id=parent.id)
        
        assert child.parent_id == parent.id
        assert manager.parent_child_graph[child.id] == parent.id
    
    def test_prevent_circular_delegation(self):
        """Test prevention of circular delegation"""
        manager = AgentManager()
        agent_a = manager.spawn_agent("a", "Task A")
        agent_b = manager.spawn_agent("b", "Task B", parent_id=agent_a.id)
        
        # Try to make A child of B (circular)
        with pytest.raises(ValueError):
            manager.spawn_agent("c", "Task C", parent_id=agent_b.id, parent_of=agent_a.id)
    
    def test_cleanup_agent(self):
        """Test agent cleanup"""
        manager = AgentManager()
        agent = manager.spawn_agent("test", "Task")
        agent.status = "complete"
        
        manager.cleanup_agent(agent.id)
        
        assert agent.id not in manager.agents
    
    def test_list_active_agents(self):
        """Test listing active agents"""
        manager = AgentManager()
        agent1 = manager.spawn_agent("a", "Task 1")
        agent2 = manager.spawn_agent("b", "Task 2")
        
        active = manager.list_active_agents()
        
        assert len(active) == 2
        assert agent1 in active
        assert agent2 in active
    
    def test_count_agents(self):
        """Test agent count"""
        manager = AgentManager()
        
        assert manager.count_agents() == 0
        
        manager.spawn_agent("a", "Task")
        manager.spawn_agent("b", "Task")
        
        assert manager.count_agents() == 2
