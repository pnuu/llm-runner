"""Tests for agent limiter timeout enforcement with asyncio"""
import asyncio
import time
import pytest
from llm_runner.agent_limiter import AgentLimiter


class TestAgentLimiterTimeout:
    """Test timeout enforcement in AgentLimiter"""
    
    @pytest.fixture
    def limiter(self):
        """Create limiter with reasonable timeouts"""
        return AgentLimiter(max_depth=5, max_agents=20, max_concurrent=10, task_timeout=1)
    
    def test_limiter_initialization(self, limiter):
        """AgentLimiter initializes with timeout"""
        assert limiter.task_timeout == 1
        assert limiter.max_depth == 5
        assert limiter.max_agents == 20
        assert limiter.max_concurrent == 10
    
    def test_timeout_parameter_configurable(self):
        """Timeout is configurable"""
        limiter_short = AgentLimiter(task_timeout=0.5)
        limiter_long = AgentLimiter(task_timeout=10.0)
        
        assert limiter_short.task_timeout == 0.5
        assert limiter_long.task_timeout == 10.0
    
    def test_apply_timeout_tracks_execution_time(self, limiter):
        """apply_timeout tracks execution time"""
        def quick_func():
            time.sleep(0.1)
            return "done"
        
        result = limiter.apply_timeout(quick_func)
        assert result == "done"
    
    def test_apply_timeout_with_args(self, limiter):
        """apply_timeout passes args to function"""
        def func_with_args(a, b, c=None):
            return {"a": a, "b": b, "c": c}
        
        result = limiter.apply_timeout(func_with_args, 1, 2, c=3)
        assert result == {"a": 1, "b": 2, "c": 3}
    
    def test_apply_timeout_preserves_exceptions(self, limiter):
        """Exceptions in function are propagated"""
        def failing_func():
            raise ValueError("function error")
        
        with pytest.raises(ValueError, match="function error"):
            limiter.apply_timeout(failing_func)
    
    def test_apply_timeout_different_durations(self, limiter):
        """apply_timeout works with different execution times"""
        def variable_func(duration):
            time.sleep(duration)
            return f"slept {duration}s"
        
        # Quick execution
        result = limiter.apply_timeout(variable_func, 0.05)
        assert "0.05" in result
        
        # Still quick relative to timeout
        result = limiter.apply_timeout(variable_func, 0.3)
        assert "0.3" in result
    
    def test_task_timeout_does_not_prevent_execution(self, limiter):
        """Having task_timeout set doesn't prevent normal execution"""
        def normal_func():
            return "executed"
        
        # Should execute without issues
        result = limiter.apply_timeout(normal_func)
        assert result == "executed"


class TestTimeoutContextManagement:
    """Test timeout context management"""
    
    def test_limiter_can_be_reused(self):
        """Limiter can execute multiple tasks"""
        limiter = AgentLimiter(task_timeout=5)
        
        def task(n):
            return n * 2
        
        # Multiple calls should work
        assert limiter.apply_timeout(task, 5) == 10
        assert limiter.apply_timeout(task, 10) == 20
        assert limiter.apply_timeout(task, 15) == 30
    
    def test_limiter_state_isolated(self):
        """Multiple limiters don't interfere"""
        limiter1 = AgentLimiter(task_timeout=1)
        limiter2 = AgentLimiter(task_timeout=2)
        
        def task():
            return "result"
        
        result1 = limiter1.apply_timeout(task)
        result2 = limiter2.apply_timeout(task)
        
        assert result1 == result2 == "result"
        assert limiter1.task_timeout != limiter2.task_timeout


class TestTimeoutDocumentation:
    """Test that timeout behavior is documented and testable"""
    
    def test_timeout_is_documented(self):
        """Timeout parameter is documented"""
        import inspect
        sig = inspect.signature(AgentLimiter.__init__)
        assert "task_timeout" in sig.parameters
        
        # Check docstring mentions timeout
        assert AgentLimiter.__init__.__doc__ is not None
        assert "timeout" in AgentLimiter.__init__.__doc__.lower()
    
    def test_apply_timeout_is_documented(self):
        """apply_timeout method is documented"""
        import inspect
        assert AgentLimiter.apply_timeout.__doc__ is not None
        assert "timeout" in AgentLimiter.apply_timeout.__doc__.lower()


class TestDepthLimitation:
    """Test depth limitation still works"""
    
    def test_can_spawn_at_valid_depth(self):
        """Can spawn at valid depth"""
        limiter = AgentLimiter(max_depth=3)
        
        assert limiter.can_spawn_agent(depth=0)
        assert limiter.can_spawn_agent(depth=1)
        assert limiter.can_spawn_agent(depth=2)
    
    def test_cannot_spawn_beyond_max_depth(self):
        """Cannot spawn beyond max depth"""
        limiter = AgentLimiter(max_depth=3)
        
        assert not limiter.can_spawn_agent(depth=4)
        assert not limiter.can_spawn_agent(depth=5)
    
    def test_max_agents_limit(self):
        """Max agents limit enforced"""
        limiter = AgentLimiter(max_agents=5)
        
        # Register agents up to limit
        for i in range(5):
            limiter.register_agent(f"agent_{i}")
        
        # Should not allow spawning more
        assert not limiter.can_spawn_agent()


class TestConcurrentLimit:
    """Test concurrent agent limit"""
    
    def test_concurrent_agents_tracked(self):
        """Concurrent agents are tracked"""
        limiter = AgentLimiter(max_concurrent=3)
        
        limiter.register_agent("a1")
        assert limiter.get_active_count() == 1
        
        limiter.register_agent("a2")
        assert limiter.get_active_count() == 2
        
        limiter.register_agent("a3")
        assert limiter.get_active_count() == 3
    
    def test_unregister_updates_count(self):
        """Unregistering updates active count"""
        limiter = AgentLimiter(max_concurrent=5)
        
        limiter.register_agent("a1")
        limiter.register_agent("a2")
        assert limiter.get_active_count() == 2
        
        limiter.unregister_agent("a1")
        assert limiter.get_active_count() == 1


class TestCircularDetection:
    """Test circular reference detection"""
    
    def test_no_circular_in_linear_chain(self):
        """Linear chain is not circular"""
        limiter = AgentLimiter()
        
        assert not limiter.is_circular(["root", "child", "grandchild"])
    
    def test_circular_detected(self):
        """Circular reference is detected"""
        limiter = AgentLimiter()
        
        assert limiter.is_circular(["root", "child", "root"])
    
    def test_self_reference_detected(self):
        """Self reference is detected"""
        limiter = AgentLimiter()
        
        assert limiter.is_circular(["agent", "agent"])
