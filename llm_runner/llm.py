"""LLM integration module for Ollama"""
import requests
import asyncio
import json
import inspect
from typing import Optional, Callable, AsyncIterator, Any
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from llm_runner.async_executor import TimeoutError as AsyncTimeoutError


class OllamaClient:
    """Client for communicating with Ollama LLM API"""
    
    def __init__(self, url="http://localhost:11434"):
        """Initialize Ollama client
        
        Args:
            url: Ollama API endpoint URL
        """
        self.url = url
        self._context_length_cache = {}
    
    def send_prompt(self, prompt, model="mistral", temperature=0.7):
        """Send a prompt to Ollama and get response
        
        Args:
            prompt: User prompt text
            model: Model name to use
            temperature: Temperature parameter for response generation
            
        Returns:
            Response text from the model, or error message if failed
        """
        endpoint = f"{self.url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=120)
            result = response.json()
            
            # Check for API errors
            if "error" in result:
                error_msg = result.get("error", "Unknown error")
                return f"[Error from model: {error_msg}]"
            
            return result.get("response", "[No response from model]")
        except requests.exceptions.Timeout:
            return "[Error: Request timed out. Model may be slow or unavailable.]"
        except requests.exceptions.RequestException as e:
            return f"[Error: Connection failed: {str(e)}]"
        except Exception as e:
            return f"[Error: {str(e)}]"
    
    async def send_prompt_async(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        timeout_sec: Optional[float] = None
    ) -> str:
        """Send a prompt to Ollama asynchronously with timeout support
        
        Args:
            prompt: User prompt text
            model: Model name to use
            temperature: Temperature parameter for response generation
            timeout_sec: Timeout in seconds (uses asyncio default if None)
            
        Returns:
            Response text from the model, or error message if failed
        """
        if not HAS_HTTPX:
            return "[Error: httpx required for async operations. Install with: pip install httpx]"
        
        endpoint = f"{self.url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        timeout = timeout_sec if timeout_sec is not None else 120.0
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, json=payload)
                result = response.json()
                
                if "error" in result:
                    error_msg = result.get("error", "Unknown error")
                    return f"[Error from model: {error_msg}]"
                
                return result.get("response", "[No response from model]")
        except asyncio.TimeoutError:
            return "[Error: Request timed out (async). Model may be slow or unavailable.]"
        except httpx.TimeoutException:
            return "[Error: Request timed out (httpx). Model may be slow or unavailable.]"
        except Exception as e:
            return f"[Error: {str(e)}]"
    
    async def send_prompt_streaming(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        on_chunk_callback: Optional[Callable[[dict], Any]] = None
    ) -> AsyncIterator[dict]:
        """Send a prompt to Ollama and stream the response
        
        Args:
            prompt: User prompt text
            model: Model name to use
            temperature: Temperature parameter for response generation
            on_chunk_callback: Optional callback function called for each chunk
            
        Yields:
            Response chunks as dicts with "response" field
        """
        if not HAS_HTTPX:
            yield {"error": "httpx required for streaming. Install with: pip install httpx"}
            return
        
        endpoint = f"{self.url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", endpoint, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if on_chunk_callback:
                                    await self._call_callback(on_chunk_callback, chunk)
                                yield chunk
                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue
        except Exception as e:
            yield {"error": str(e)}
    
    async def _call_callback(self, callback: Callable, chunk: dict) -> None:
        """Call callback, handling both sync and async callbacks
        
        Args:
            callback: Function to call with chunk
            chunk: Data to pass to callback
        """
        if inspect.iscoroutinefunction(callback):
            await callback(chunk)
        else:
            callback(chunk)
    
    def get_model_context_length(self, model_name):
        """Get context length (max tokens) for a model
        
        Args:
            model_name: Name of the model (e.g., "mistral:7b")
            
        Returns:
            Context length in tokens, or 4096 if unable to determine
        """
        # Check cache first
        if model_name in self._context_length_cache:
            return self._context_length_cache[model_name]
        
        try:
            endpoint = f"{self.url}/api/show"
            payload = {"name": model_name}
            
            response = requests.post(endpoint, json=payload, timeout=10)
            data = response.json()
            
            # Try to get context length from model_info
            model_info = data.get("model_info", {})
            context_length = model_info.get("llama.context_length")
            
            if context_length is None:
                # Fallback to default
                context_length = 4096
            
            # Cache the result
            self._context_length_cache[model_name] = context_length
            return context_length
            
        except Exception:
            # On any error, return default and cache it
            self._context_length_cache[model_name] = 4096
            return 4096


def get_available_models(url="http://localhost:11434"):
    """Get list of available models from Ollama
    
    Args:
        url: Ollama API endpoint
        
    Returns:
        List of model names, or empty list if error
    """
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        data = response.json()
        
        models = []
        if "models" in data:
            for model_info in data["models"]:
                if "name" in model_info:
                    models.append(model_info["name"])
        
        return models
    except Exception:
        return []


def check_ollama_connection(url="http://localhost:11434", timeout=5):
    """Check if Ollama is accessible
    
    Args:
        url: Ollama API endpoint
        timeout: Connection timeout in seconds
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response = requests.get(f"{url}/api/tags", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False
