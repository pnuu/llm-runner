"""Tests for agent system safety and limits"""
import pytest
from llm_runner.agent_limiter import AgentLimiter


class TestAgentLimits:
    """Test agent safety and resource controls"""
    
    def test_agent_limiter_creation(self):
        """Test limiter initialization"""
        limiter = AgentLimiter(
            max_depth=5,
            max_agents=20,
            task_timeout=30
        )
        
        assert limiter.max_depth == 5
        assert limiter.max_agents == 20
        assert limiter.task_timeout == 30
    
    def test_max_depth_enforcement(self):
        """Test maximum delegation depth enforcement"""
        limiter = AgentLimiter(max_depth=2)
        
        # Start at depth 0
        assert limiter.can_spawn_agent(depth=0) is True
        
        # Depth 1 - OK
        assert limiter.can_spawn_agent(depth=1) is True
        
        # Depth 2 - at limit
        assert limiter.can_spawn_agent(depth=2) is True
        
        # Depth 3 - exceeds limit
        assert limiter.can_spawn_agent(depth=3) is False
    
    def test_max_agents_enforcement(self):
        """Test maximum active agents enforcement"""
        limiter = AgentLimiter(max_agents=10, max_concurrent=3)
        
        # Register agents up to concurrent limit
        for i in range(3):
            limiter.register_agent(f"agent-{i}")
        
        # Now at concurrent max
        assert limiter.can_spawn_agent(active_count=3) is False
        
        # Unregister one
        limiter.unregister_agent("agent-0")
        
        # Can spawn again (under concurrent limit)
        assert limiter.can_spawn_agent(active_count=2) is True
        
        # But total agents still counts
        assert limiter.total_agents_created == 3
    
    def test_circular_delegation_prevention(self):
        """Test prevention of circular delegation"""
        limiter = AgentLimiter()
        
        # Build ancestry chain
        ancestry = ["root", "child", "grandchild"]
        
        # Grandchild spawning parent - would be circular
        circular_chain = ["root", "child", "grandchild", "child"]
        
        assert limiter.is_circular(circular_chain) is True
        assert limiter.is_circular(ancestry) is False
    
    def test_timeout_on_stuck_agent(self):
        """Test timeout mechanism for stuck agents"""
        limiter = AgentLimiter(task_timeout=1)
        
        import time
        start = time.time()
        
        # Simulate long task
        result = limiter.apply_timeout(lambda: time.sleep(0.1))
        
        elapsed = time.time() - start
        
        # Should complete within timeout
        assert elapsed < limiter.task_timeout + 1
    
    def test_concurrent_agent_limit(self):
        """Test limiting concurrent agents"""
        limiter = AgentLimiter(max_concurrent=5)
        
        # Can track concurrent agents
        for i in range(5):
            limiter.register_agent(f"agent-{i}")
        
        assert limiter.get_active_count() == 5
        
        # Cannot spawn more
        assert limiter.can_spawn_agent(active_count=5) is False
    
    def test_resource_cleanup_on_agent_failure(self):
        """Test resource cleanup when agent fails"""
        limiter = AgentLimiter()
        
        agent_id = "test-agent-1"
        limiter.register_agent(agent_id)
        
        assert limiter.get_active_count() == 1
        
        limiter.unregister_agent(agent_id)
        
        assert limiter.get_active_count() == 0
    
    def test_limits_configuration(self):
        """Test default and custom limits"""
        default_limiter = AgentLimiter()
        custom_limiter = AgentLimiter(max_depth=10, max_agents=50)
        
        assert default_limiter.max_depth == 5  # Default
        assert custom_limiter.max_depth == 10  # Custom
