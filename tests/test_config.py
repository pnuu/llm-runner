"""Test configuration module"""
import os
import tempfile
import pytest
from llm_runner.config import get_default_config, load_config, save_config, get_config_path


def test_default_config_has_required_keys():
    """Test that default config has all required keys"""
    config = get_default_config()
    assert "ollama_url" in config
    assert "model" in config
    assert "temperature" in config


def test_default_config_values():
    """Test default config has sensible defaults"""
    config = get_default_config()
    assert config["ollama_url"] == "http://localhost:11434"
    assert config["model"] == "mistral"
    assert config["temperature"] == 0.7


def test_get_config_path():
    """Test config path generation"""
    path = get_config_path()
    assert path.endswith("config.yaml")
    assert ".llm_runner" in path or "llm_runner" in path


def test_load_config_creates_default_if_missing():
    """Test that load_config creates default config if file doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.yaml")
        config = load_config(config_file)
        
        # Should return default config
        assert "ollama_url" in config
        assert "model" in config
        
        # Should create the file
        assert os.path.exists(config_file)


def test_load_config_reads_existing_file():
    """Test that load_config reads existing config file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.yaml")
        test_config = {
            "ollama_url": "http://custom:1234",
            "model": "custom-model",
            "temperature": 0.5
        }
        save_config(test_config, config_file)
        
        loaded = load_config(config_file)
        assert loaded["ollama_url"] == "http://custom:1234"
        assert loaded["model"] == "custom-model"
        assert loaded["temperature"] == 0.5


def test_save_config():
    """Test that save_config writes to YAML file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.yaml")
        test_config = {"ollama_url": "http://test:9999", "model": "test"}
        
        save_config(test_config, config_file)
        
        assert os.path.exists(config_file)
        with open(config_file, "r") as f:
            content = f.read()
            assert "http://test:9999" in content
            assert "test" in content
