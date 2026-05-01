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
