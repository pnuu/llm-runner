"""Configuration module for LLM Runner"""
import os
import yaml
from pathlib import Path


def get_default_config():
    """Get default configuration"""
    return {
        "ollama_url": "http://localhost:11434",
        "model": "mistral",  # Use "mistral:7b" if standard mistral not available
        "temperature": 0.7,
    }


def get_config_path():
    """Get the path to the config file"""
    home = Path.home()
    config_dir = home / ".llm_runner"
    return str(config_dir / "config.yaml")


def save_config(config, path=None):
    """Save configuration to YAML file"""
    if path is None:
        path = get_config_path()
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_config(path=None):
    """Load configuration from YAML file, create default if missing"""
    if path is None:
        path = get_config_path()
    
    # If file doesn't exist, create it with defaults
    if not os.path.exists(path):
        default = get_default_config()
        save_config(default, path)
        return default
    
    # Load from file
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    
    return config if config else get_default_config()
