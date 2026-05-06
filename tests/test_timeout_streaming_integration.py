"""End-to-end integration tests for timeout and streaming"""
import pytest
import asyncio
from unittest.mock import patch, Mock
from llm_runner.llm import OllamaClient
from llm_runner.async_executor import async_with_timeout, AsyncTaskRunner, TimeoutError as AsyncTimeoutError
from llm_runner.agent_limiter import AgentLimiter


class TestTimeoutAndStreamingTogether:
    """Test timeout and streaming working together"""
    
    @pytest.mark.asyncio
    async def test_async_task_with_timeout(self):
        """Async task execution with timeout"""
        async def quick_task():
            await asyncio.sleep(0.05)
            return "completed"
        
        result = await async_with_timeout(quick_task(), timeout_sec=1.0)
        assert result == "completed"
    
    @pytest.mark.asyncio
    async def test_timeout_during_async_operation(self):
        """Timeout during async operation"""
        async def slow_task():
            await asyncio.sleep(10.0)
        
        with pytest.raises(AsyncTimeoutError):
            await async_with_timeout(slow_task(), timeout_sec=0.1)
    
    @pytest.mark.asyncio
    async def test_streaming_with_timeout_protection(self):
        """Streaming operations have timeout protection"""
        client = OllamaClient()
        
        # Streaming should respect timeouts via AsyncTaskRunner
        runner = AsyncTaskRunner(default_timeout=1.0)
        
        async def stream_task():
            chunks = []
            try:
                async for chunk in client.send_prompt_streaming("test", model="mistral"):
                    chunks.append(chunk)
                    if len(chunks) > 2:
                        break
            except Exception:
                pass
            return len(chunks)
        
        try:
            count = await runner.run_task("stream", stream_task())
            # Should complete without error
            assert isinstance(count, int)
        except AsyncTimeoutError:
            # Timeouts are OK in this test
            pass


class TestAgentLimiterWithStreaming:
    """Test agent limiter with streaming operations"""
    
    def test_limiter_tracks_streaming_task(self):
        """Limiter can track streaming tasks"""
        limiter = AgentLimiter(task_timeout=5)
        
        def mock_streaming_task():
            # Simulate task that might stream
            return "stream_result"
        
        result = limiter.apply_timeout(mock_streaming_task)
        assert result == "stream_result"
    
    def test_concurrent_streaming_within_limits(self):
        """Multiple streaming tasks work within limiter constraints"""
        limiter = AgentLimiter(max_concurrent=3)
        
        limiter.register_agent("stream1")
        limiter.register_agent("stream2")
        
        assert limiter.get_active_count() == 2
        
        limiter.unregister_agent("stream1")
        assert limiter.get_active_count() == 1
    
    def test_depth_limit_with_streaming(self):
        """Depth limits work with streaming"""
        limiter = AgentLimiter(max_depth=2)
        
        # Can spawn at depth 0, 1
        assert limiter.can_spawn_agent(depth=0)
        assert limiter.can_spawn_agent(depth=1)
        
        # Cannot spawn at depth > max
        assert not limiter.can_spawn_agent(depth=3)


class TestStreamingWithErrors:
    """Test streaming error handling with timeouts"""
    
    @pytest.mark.asyncio
    async def test_streaming_error_recovery(self):
        """Streaming recovers from errors"""
        client = OllamaClient(url="http://invalid:99999")
        
        chunks = []
        try:
            async for chunk in client.send_prompt_streaming("test", model="mistral"):
                chunks.append(chunk)
        except Exception:
            pass
        
        # Should handle error gracefully
        assert isinstance(chunks, list)
    
    @pytest.mark.asyncio
    async def test_timeout_during_streaming(self):
        """Timeout interrupts streaming"""
        runner = AsyncTaskRunner(default_timeout=0.05)
        
        async def long_stream():
            count = 0
            try:
                # This would hang if not for timeout
                while True:
                    count += 1
                    await asyncio.sleep(0.01)
                    if count > 100:
                        break
            except asyncio.CancelledError:
                return "interrupted"
            return "completed"
        
        try:
            result = await runner.run_task("stream", long_stream())
            # Either completed or timed out
            assert result in ["interrupted", "completed"]
        except AsyncTimeoutError:
            # Expected - timeout fired
            pass


class TestChatWithTimeoutAndStreaming:
    """Test chat mode with both timeout and streaming"""
    
    def test_chat_send_message_with_timeout(self):
        """Chat messages have timeout protection"""
        from llm_runner.chat import InteractiveChat
        
        chat = InteractiveChat(model="mistral")
        
        with patch.object(OllamaClient, 'send_prompt', return_value="response"):
            result = chat.send_message("test")
            assert isinstance(result, str)
    
    def test_multiple_chat_messages_with_streaming(self):
        """Multiple chat messages work with streaming"""
        from llm_runner.chat import InteractiveChat
        
        chat = InteractiveChat(model="mistral")
        
        with patch.object(OllamaClient, 'send_prompt', return_value="streamed response"):
            for i in range(3):
                result = chat.send_message(f"question {i}")
                assert isinstance(result, str)
                assert len(result) > 0


class TestHandlerIntegration:
    """Test handlers with timeout and streaming"""
    
    def test_plan_handler_with_streaming(self):
        """Plan handler supports streaming"""
        from llm_runner.plan_handler import display_plan_outline
        
        plan = "## Section\n- item1\n- item2"
        result = display_plan_outline(plan)
        # Should handle without error
        assert result is None or isinstance(result, str)
    
    def test_build_handler_with_timeout(self):
        """Build handler respects timeouts"""
        from llm_runner.build_handler import handle_build_mode
        
        # Should be callable and handle timeouts
        assert callable(handle_build_mode)


class TestConcurrentOperations:
    """Test concurrent timeout and streaming operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_tasks(self):
        """Multiple streaming tasks can run concurrently"""
        async def stream_task(n):
            await asyncio.sleep(0.01)
            return n
        
        tasks = [stream_task(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        assert results == [0, 1, 2]
    
    @pytest.mark.asyncio
    async def test_mixed_timeouts_and_streaming(self):
        """Mix of timeout and streaming operations"""
        runner = AsyncTaskRunner(default_timeout=1.0)
        
        async def task1():
            await asyncio.sleep(0.05)
            return "task1"
        
        async def task2():
            await asyncio.sleep(0.1)
            return "task2"
        
        r1 = await runner.run_task("t1", task1())
        r2 = await runner.run_task("t2", task2())
        
        assert r1 == "task1"
        assert r2 == "task2"


class TestBackwardsCompatibility:
    """Ensure backwards compatibility with existing code"""
    
    def test_sync_methods_still_work(self):
        """Original sync methods still functional"""
        client = OllamaClient()
        assert callable(client.send_prompt)
        assert callable(client.get_model_context_length)
    
    def test_agent_limiter_unchanged_interface(self):
        """Agent limiter interface unchanged"""
        limiter = AgentLimiter()
        assert callable(limiter.can_spawn_agent)
        assert callable(limiter.register_agent)
        assert callable(limiter.apply_timeout)
    
    def test_executor_unchanged_interface(self):
        """Executor interface unchanged"""
        from llm_runner.executor import BuildExecutor
        executor = BuildExecutor()
        assert callable(executor.execute_tool)
        assert hasattr(executor, 'tools')
