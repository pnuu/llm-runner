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
        "chat": {
            "ui": {
                "colors": {
                    "user_message": "light_gray",
                    "ai_message": "white",
                    "status_line": "cyan",
                    "command_window": "white",
                },
                "show_status_line": True,
                "show_command_window": True,
            }
        }
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
    
    if not config:
        config = {}
    
    # Merge with defaults to ensure all keys exist
    merged = get_default_config()
    _deep_merge(merged, config)
    
    return merged


def _deep_merge(base, override):
    """Recursively merge override dict into base dict (in-place).
    
    Args:
        base: Base dictionary (modified in-place)
        override: Dictionary with overrides
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_chat_colors(config):
    """Get chat UI color configuration from config.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dictionary with color settings, defaults applied
    """
    try:
        colors = config.get("chat", {}).get("ui", {}).get("colors", {})
        # Return with defaults filled in
        defaults = get_default_config()["chat"]["ui"]["colors"]
        merged = defaults.copy()
        merged.update(colors)
        return merged
    except (KeyError, TypeError, AttributeError):
        # Fall back to defaults if anything goes wrong
        return get_default_config()["chat"]["ui"]["colors"]
