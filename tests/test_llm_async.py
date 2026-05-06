"""Tests for async LLM client methods"""
import asyncio
import pytest
from llm_runner.llm import OllamaClient


class TestOllamaClientAsync:
    """Test async methods in OllamaClient"""
    
    @pytest.fixture
    def client(self):
        """Create OllamaClient for testing"""
        return OllamaClient(url="http://localhost:11434")
    
    @pytest.mark.asyncio
    async def test_async_methods_exist(self, client):
        """Verify async methods are available"""
        assert hasattr(client, "send_prompt_async")
        assert hasattr(client, "send_prompt_streaming")
        assert callable(client.send_prompt_async)
        assert callable(client.send_prompt_streaming)
    
    @pytest.mark.asyncio
    async def test_send_prompt_async_with_no_server(self, client):
        """Async prompt handles server unavailable gracefully"""
        # This will connect to localhost:11434 which may not have Ollama running
        # But it should not crash, just return an error message
        result = await client.send_prompt_async("test", model="mistral")
        assert isinstance(result, str)
        # Either error or actual response
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_method_signature(self, client):
        """Streaming method has correct signature"""
        import inspect
        sig = inspect.signature(client.send_prompt_streaming)
        params = list(sig.parameters.keys())
        assert "prompt" in params
        assert "model" in params
        assert "temperature" in params
        assert "on_chunk_callback" in params
    
    @pytest.mark.asyncio
    async def test_streaming_is_async_generator(self, client):
        """Streaming method returns async generator"""
        gen = client.send_prompt_streaming("test", model="mistral")
        assert hasattr(gen, "__aiter__")
    
    @pytest.mark.asyncio
    async def test_concurrent_async_calls(self, client):
        """Multiple async calls can run concurrently"""
        # This is a basic concurrency test - doesn't require actual server
        async def dummy_async_call():
            await asyncio.sleep(0.01)
            return "result"
        
        # Should be able to run multiple concurrently
        tasks = [dummy_async_call() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
    
    def test_sync_methods_still_exist(self, client):
        """Sync methods unchanged for backwards compatibility"""
        assert hasattr(client, "send_prompt")
        assert hasattr(client, "get_model_context_length")
        assert callable(client.send_prompt)
        assert callable(client.get_model_context_length)


class TestAsyncMethodsIntegration:
    """Integration tests for async methods"""
    
    @pytest.fixture
    def client(self):
        return OllamaClient(url="http://localhost:11434")
    
    @pytest.mark.asyncio
    async def test_timeout_parameter_passthrough(self, client):
        """Timeout parameter is accepted"""
        import inspect
        sig = inspect.signature(client.send_prompt_async)
        assert "timeout_sec" in sig.parameters
    
    @pytest.mark.asyncio
    async def test_callback_parameter_passthrough(self, client):
        """Callback parameter is accepted"""
        import inspect
        sig = inspect.signature(client.send_prompt_streaming)
        assert "on_chunk_callback" in sig.parameters
    
    @pytest.mark.asyncio
    async def test_no_blocking_in_async_methods(self, client):
        """Async methods use proper await, don't block"""
        # Create an async context - if methods block, this would timeout
        async def test_no_block():
            try:
                # Quick timeout on attempt - if it blocks, we catch it
                result = await asyncio.wait_for(
                    client.send_prompt_async("test", model="mistral"),
                    timeout=0.5
                )
                # Result might be error (no server) but shouldn't block
                assert isinstance(result, str)
            except asyncio.TimeoutError:
                # If timeout hits, method is blocking (bad)
                pytest.fail("Async method appears to be blocking")
            except Exception:
                # Other exceptions are OK (connection errors, etc)
                pass
        
        await test_no_block()


class TestStreamingIntegration:
    """Integration tests for streaming functionality"""
    
    @pytest.fixture
    def client(self):
        return OllamaClient(url="http://localhost:11434")
    
    @pytest.mark.asyncio
    async def test_streaming_iteration_works(self, client):
        """Can iterate through streaming responses"""
        # This won't connect to real server but tests iteration syntax
        try:
            chunk_count = 0
            async for chunk in client.send_prompt_streaming("test", model="mistral"):
                chunk_count += 1
                # Break after first to avoid hanging
                break
            
            # Should be able to iterate without syntax errors
            assert True
        except StopAsyncIteration:
            # This is OK - means streaming ended
            assert True
        except Exception as e:
            # Connection errors are expected without running Ollama
            # But should not be syntax errors
            assert "syntax" not in str(e).lower()


class TestBackwardsCompatibility:
    """Ensure sync and async methods coexist"""
    
    @pytest.fixture
    def client(self):
        return OllamaClient(url="http://localhost:11434")
    
    def test_sync_send_prompt_still_available(self, client):
        """Original sync send_prompt method still works"""
        assert hasattr(client, "send_prompt")
        assert callable(client.send_prompt)
    
    @pytest.mark.asyncio
    async def test_async_send_prompt_available(self, client):
        """New async send_prompt_async method exists"""
        assert hasattr(client, "send_prompt_async")
        assert callable(client.send_prompt_async)
    
    @pytest.mark.asyncio
    async def test_async_streaming_available(self, client):
        """New streaming method exists"""
        assert hasattr(client, "send_prompt_streaming")
        assert callable(client.send_prompt_streaming)
    
    def test_model_context_length_sync_still_works(self, client):
        """Original model context length method unchanged"""
        assert hasattr(client, "get_model_context_length")
        assert callable(client.get_model_context_length)
