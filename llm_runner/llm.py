"""LLM integration module for Ollama"""
import requests


class OllamaClient:
    """Client for communicating with Ollama LLM API"""
    
    def __init__(self, url="http://localhost:11434"):
        """Initialize Ollama client
        
        Args:
            url: Ollama API endpoint URL
        """
        self.url = url
    
    def send_prompt(self, prompt, model="mistral", temperature=0.7):
        """Send a prompt to Ollama and get response
        
        Args:
            prompt: User prompt text
            model: Model name to use
            temperature: Temperature parameter for response generation
            
        Returns:
            Response text from the model
        """
        endpoint = f"{self.url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        response = requests.post(endpoint, json=payload)
        result = response.json()
        
        return result.get("response", "")


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
