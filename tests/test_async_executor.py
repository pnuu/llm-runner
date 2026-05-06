"""Tests for async task execution with timeout enforcement"""
import asyncio
import pytest
import time
from llm_runner.async_executor import async_with_timeout, AsyncTaskRunner, TimeoutError as AsyncTimeoutError


class TestAsyncWithTimeout:
    """Test async_with_timeout() wrapper function"""
    
    @pytest.mark.asyncio
    async def test_successful_completion_within_timeout(self):
        """Task completes successfully before timeout"""
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await async_with_timeout(quick_task(), timeout_sec=1.0)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_enforced(self):
        """Task is cancelled when it exceeds timeout"""
        async def slow_task():
            await asyncio.sleep(5.0)
            return "done"
        
        with pytest.raises(AsyncTimeoutError):
            await async_with_timeout(slow_task(), timeout_sec=0.1)
    
    @pytest.mark.asyncio
    async def test_immediate_cancellation(self):
        """Immediate cancellation on timeout"""
        start = time.time()
        
        async def slow_task():
            await asyncio.sleep(10.0)
        
        with pytest.raises(AsyncTimeoutError):
            await async_with_timeout(slow_task(), timeout_sec=0.05)
        
        elapsed = time.time() - start
        # Should timeout around 0.05s, not 10s
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_return_value_preserved(self):
        """Successful completion returns correct value"""
        async def task_with_value():
            return {"result": "data", "count": 42}
        
        result = await async_with_timeout(task_with_value(), timeout_sec=1.0)
        assert result == {"result": "data", "count": 42}
    
    @pytest.mark.asyncio
    async def test_exception_from_task_propagated(self):
        """Exceptions in task are propagated"""
        async def failing_task():
            raise ValueError("task failed")
        
        with pytest.raises(ValueError, match="task failed"):
            await async_with_timeout(failing_task(), timeout_sec=1.0)
    
    @pytest.mark.asyncio
    async def test_zero_timeout(self):
        """Zero timeout immediately raises"""
        async def task():
            await asyncio.sleep(0.1)
        
        with pytest.raises(AsyncTimeoutError):
            await async_with_timeout(task(), timeout_sec=0.0)


class TestAsyncTaskRunner:
    """Test AsyncTaskRunner class for concurrent task management"""
    
    @pytest.mark.asyncio
    async def test_single_task_success(self):
        """Run single task successfully"""
        async def task():
            return "result"
        
        runner = AsyncTaskRunner(default_timeout=5.0)
        result = await runner.run_task("task1", task())
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_single_task_timeout(self):
        """Single task times out"""
        async def slow_task():
            await asyncio.sleep(10.0)
        
        runner = AsyncTaskRunner(default_timeout=0.1)
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("task1", slow_task())
    
    @pytest.mark.asyncio
    async def test_task_with_custom_timeout(self):
        """Task timeout can override default"""
        async def task():
            await asyncio.sleep(0.2)
            return "done"
        
        runner = AsyncTaskRunner(default_timeout=1.0)
        # Uses default, should succeed
        result = await runner.run_task("task1", task())
        assert result == "done"
        
        # Uses custom short timeout, should fail
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("task2", task(), timeout_sec=0.05)
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks(self):
        """Run multiple tasks concurrently"""
        async def task(n):
            await asyncio.sleep(0.1)
            return n * 2
        
        runner = AsyncTaskRunner(default_timeout=5.0)
        results = await asyncio.gather(
            runner.run_task("t1", task(5)),
            runner.run_task("t2", task(10)),
            runner.run_task("t3", task(15)),
        )
        
        assert results == [10, 20, 30]
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks_with_timeout(self):
        """Concurrent tasks with mixed success/timeout"""
        async def quick_task(n):
            await asyncio.sleep(0.05)
            return n
        
        async def slow_task(n):
            await asyncio.sleep(5.0)
            return n
        
        runner = AsyncTaskRunner(default_timeout=0.2)
        
        # Quick tasks succeed
        result1 = await runner.run_task("t1", quick_task(1))
        assert result1 == 1
        
        # Slow task times out
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("t2", slow_task(2))
    
    @pytest.mark.asyncio
    async def test_task_cleanup_on_timeout(self):
        """Resources are cleaned up on timeout"""
        cleanup_called = []
        
        async def task_with_cleanup():
            try:
                await asyncio.sleep(10.0)
            except asyncio.CancelledError:
                cleanup_called.append(True)
                raise
        
        runner = AsyncTaskRunner(default_timeout=0.05)
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("task", task_with_cleanup())
        
        # Give task a moment to handle cancellation
        await asyncio.sleep(0.01)
        assert len(cleanup_called) > 0
    
    @pytest.mark.asyncio
    async def test_context_manager_interface(self):
        """AsyncTaskRunner can be used as context manager"""
        async def task():
            return "result"
        
        runner = AsyncTaskRunner(default_timeout=5.0)
        result = await runner.run_task("task", task())
        assert result == "result"


class TestTimeoutErrorException:
    """Test AsyncTimeoutError exception"""
    
    def test_timeout_error_inherits_from_exception(self):
        """TimeoutError is proper exception"""
        exc = AsyncTimeoutError("test timeout")
        assert isinstance(exc, Exception)
        assert str(exc) == "test timeout"
    
    def test_timeout_error_can_be_caught(self):
        """TimeoutError can be caught by exception handlers"""
        try:
            raise AsyncTimeoutError("operation timeout")
        except AsyncTimeoutError as e:
            assert "operation timeout" in str(e)
        except Exception:
            pytest.fail("Should catch AsyncTimeoutError")


class TestIntegrationScenarios:
    """Integration tests combining timeout and streaming"""
    
    @pytest.mark.asyncio
    async def test_rapid_successive_tasks(self):
        """Run many quick tasks in succession"""
        async def task(n):
            return n * 2
        
        runner = AsyncTaskRunner(default_timeout=5.0)
        results = []
        for i in range(10):
            result = await runner.run_task(f"task_{i}", task(i))
            results.append(result)
        
        assert results == [n * 2 for n in range(10)]
    
    @pytest.mark.asyncio
    async def test_timeout_during_task_sequence(self):
        """Some tasks timeout in sequence"""
        async def quick_task():
            await asyncio.sleep(0.05)
            return "ok"
        
        async def slow_task():
            await asyncio.sleep(5.0)
            return "ok"
        
        runner = AsyncTaskRunner(default_timeout=0.2)
        
        # First few succeed
        assert await runner.run_task("t1", quick_task()) == "ok"
        assert await runner.run_task("t2", quick_task()) == "ok"
        
        # This times out
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("t3", slow_task())
        
        # Can continue with new tasks
        assert await runner.run_task("t4", quick_task()) == "ok"
    
    @pytest.mark.asyncio
    async def test_mixed_success_and_timeout_gathering(self):
        """Gather with some successes and some timeouts"""
        async def task(duration):
            await asyncio.sleep(duration)
            return f"done_{duration}"
        
        runner = AsyncTaskRunner(default_timeout=0.3)
        
        # Create tasks with mixed durations
        tasks = [
            runner.run_task("fast1", task(0.1)),
            runner.run_task("slow1", task(5.0)),  # Will timeout
            runner.run_task("fast2", task(0.1)),
        ]
        
        # First one succeeds
        result1 = await runner.run_task("fast1", task(0.1))
        assert result1 == "done_0.1"
        
        # Second times out
        with pytest.raises(AsyncTimeoutError):
            await runner.run_task("slow", task(5.0))
        
        # Third succeeds
        result3 = await runner.run_task("fast2", task(0.1))
        assert result3 == "done_0.1"
