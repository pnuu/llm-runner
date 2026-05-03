"""Interactive configuration wizard for LLM-Runner"""
from pathlib import Path
from typing import Optional, Dict, List, Any
import yaml
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class ConfigWizard:
    """Interactive configuration setup and management"""
    
    DEFAULT_CONFIG = {
        'model': 'mistral',
        'temperature': 0.7,
        'max_tokens': 2000,
        'context_size': 4096,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize config wizard
        
        Args:
            config_file: Path to config file (default: ~/.llm_runner/config.yaml)
        """
        if config_file is None:
            config_file = str(Path.home() / ".llm_runner" / "config.yaml")
        
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load config or use defaults
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {}
        
        # Fill in missing values from defaults
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = value
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def set_model(self, model: str) -> bool:
        """Set the LLM model
        
        Args:
            model: Model name
            
        Returns:
            True if set successfully
        """
        if model and isinstance(model, str):
            self.config['model'] = model
            return True
        return False
    
    def set_temperature(self, temperature: float) -> bool:
        """Set temperature parameter
        
        Args:
            temperature: Temperature (0.0-1.0)
            
        Returns:
            True if valid and set
        """
        if self.validate_temperature(temperature):
            self.config['temperature'] = temperature
            return True
        return False
    
    def set_max_tokens(self, max_tokens: int) -> bool:
        """Set maximum tokens
        
        Args:
            max_tokens: Maximum tokens for response
            
        Returns:
            True if valid and set
        """
        if self.validate_max_tokens(max_tokens):
            self.config['max_tokens'] = max_tokens
            return True
        return False
    
    def validate_temperature(self, temperature: float) -> bool:
        """Validate temperature value
        
        Args:
            temperature: Value to validate
            
        Returns:
            True if valid (0.0 <= temp <= 1.0)
        """
        return isinstance(temperature, (int, float)) and 0.0 <= temperature <= 1.0
    
    def validate_max_tokens(self, max_tokens: int) -> bool:
        """Validate max tokens value
        
        Args:
            max_tokens: Value to validate
            
        Returns:
            True if valid (> 0)
        """
        return isinstance(max_tokens, int) and max_tokens > 0
    
    def get_available_models(self) -> List[str]:
        """Get available models from ollama
        
        Returns:
            List of available model names
        """
        if not OLLAMA_AVAILABLE:
            return []
        
        try:
            response = ollama.list()
            models = [model.model for model in response.models]
            return models
        except Exception:
            return []
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self.DEFAULT_CONFIG.copy()
    
    def save(self) -> bool:
        """Save configuration to file
        
        Returns:
            True if saved successfully
        """
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception:
            return False
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values
        
        Args:
            updates: Dictionary of values to update
        """
        for key, value in updates.items():
            if key == 'temperature':
                self.set_temperature(value)
            elif key == 'max_tokens':
                self.set_max_tokens(value)
            elif key == 'model':
                self.set_model(value)
            else:
                self.config[key] = value
    
    def interactive_setup(self) -> None:
        """Run interactive setup wizard
        
        Guides user through configuration options
        """
        print("LLM-Runner Configuration Wizard")
        print("=" * 40)
        
        # Model selection
        available = self.get_available_models()
        if available:
            print("\nAvailable models:")
            for i, model in enumerate(available, 1):
                print(f"  {i}. {model}")
            
            current = self.config.get('model', 'mistral')
            choice = input(f"\nSelect model (current: {current}): ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    self.set_model(available[idx])
        else:
            model = input("\nModel name (default: mistral): ").strip() or "mistral"
            self.set_model(model)
        
        # Temperature
        temp_str = input(f"Temperature [0-1] (default: {self.config.get('temperature', 0.7)}): ").strip()
        if temp_str:
            try:
                temp = float(temp_str)
                if self.validate_temperature(temp):
                    self.set_temperature(temp)
                else:
                    print("Invalid temperature (must be 0-1)")
            except ValueError:
                print("Invalid number")
        
        # Max tokens
        tokens_str = input(f"Max tokens (default: {self.config.get('max_tokens', 2000)}): ").strip()
        if tokens_str:
            try:
                tokens = int(tokens_str)
                if self.validate_max_tokens(tokens):
                    self.set_max_tokens(tokens)
                else:
                    print("Invalid max tokens (must be > 0)")
            except ValueError:
                print("Invalid number")
        
        # Save
        save = input("\nSave configuration? (y/n): ").strip().lower()
        if save == 'y':
            if self.save():
                print("Configuration saved!")
            else:
                print("Failed to save configuration")
    
    def print_config(self) -> None:
        """Print current configuration"""
        print("Current Configuration:")
        print("-" * 30)
        for key, value in self.config.items():
            print(f"{key}: {value}")
