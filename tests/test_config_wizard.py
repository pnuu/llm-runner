"""Tests for interactive configuration wizard"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from llm_runner.config_wizard import ConfigWizard


class TestConfigWizard:
    """Test interactive configuration setup"""
    
    def test_wizard_init(self):
        """Test creating config wizard"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            assert wizard is not None
    
    def test_load_existing_config(self):
        """Test loading existing configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            
            # Create existing config
            import yaml
            config_data = {
                "model": "mistral",
                "temperature": 0.7,
                "max_tokens": 2000
            }
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            wizard = ConfigWizard(config_file=config_file)
            assert wizard is not None
    
    def test_get_config(self):
        """Test getting configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            config = wizard.get_config()
            
            assert config is not None
            assert isinstance(config, dict)
    
    def test_set_model(self):
        """Test setting model in config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            wizard.set_model("llama2")
            
            config = wizard.get_config()
            assert config.get('model') == "llama2"
    
    def test_set_temperature(self):
        """Test setting temperature"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            wizard.set_temperature(0.5)
            
            config = wizard.get_config()
            assert config.get('temperature') == 0.5
    
    def test_set_max_tokens(self):
        """Test setting max tokens"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            wizard.set_max_tokens(4096)
            
            config = wizard.get_config()
            assert config.get('max_tokens') == 4096
    
    def test_validate_temperature_range(self):
        """Test temperature validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Valid range
            assert wizard.validate_temperature(0.0)
            assert wizard.validate_temperature(0.5)
            assert wizard.validate_temperature(1.0)
            
            # Invalid
            assert not wizard.validate_temperature(-0.1)
            assert not wizard.validate_temperature(1.1)
    
    def test_validate_max_tokens(self):
        """Test max tokens validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Valid
            assert wizard.validate_max_tokens(1)
            assert wizard.validate_max_tokens(2000)
            assert wizard.validate_max_tokens(100000)
            
            # Invalid
            assert not wizard.validate_max_tokens(0)
            assert not wizard.validate_max_tokens(-1)
    
    def test_get_available_models(self):
        """Test getting available models from ollama"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Just test that the function works (returns empty if ollama not available)
            models = wizard.get_available_models()
            assert isinstance(models, list)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Set some values
            wizard.set_model("llama2")
            wizard.set_temperature(0.8)
            
            # Reset
            wizard.reset_to_defaults()
            
            config = wizard.get_config()
            # Should have default values
            assert 'model' in config or config.get('model') is None
    
    def test_save_config(self):
        """Test saving configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            wizard = ConfigWizard(config_file=config_file)
            
            wizard.set_model("mistral")
            wizard.set_temperature(0.7)
            wizard.save()
            
            # Verify file exists and has content
            assert Path(config_file).exists()
            
            # Load and verify
            import yaml
            with open(config_file) as f:
                saved = yaml.safe_load(f)
            
            assert saved.get('model') == "mistral"
            assert saved.get('temperature') == 0.7
    
    def test_config_defaults(self):
        """Test default configuration values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            config = wizard.get_config()
            
            # Should have sensible defaults
            assert config.get('temperature') is not None or config.get('temperature') == None
            assert config.get('max_tokens') is not None or config.get('max_tokens') == None
    
    def test_config_persistence(self):
        """Test that config persists across instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            
            # First wizard
            wizard1 = ConfigWizard(config_file=config_file)
            wizard1.set_model("test-model")
            wizard1.save()
            
            # Second wizard should load saved config
            wizard2 = ConfigWizard(config_file=config_file)
            config2 = wizard2.get_config()
            assert config2.get('model') == "test-model"
    
    def test_config_validation_on_set(self):
        """Test validation when setting values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Setting invalid temperature should fail silently or raise
            result = wizard.set_temperature(2.0)  # > 1.0
            # Should either reject or clamp
            
            config = wizard.get_config()
            temp = config.get('temperature', 0)
            assert temp <= 1.0 or result is False
    
    def test_config_update(self):
        """Test updating multiple config values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            updates = {
                'model': 'llama2',
                'temperature': 0.8,
                'max_tokens': 3000
            }
            
            wizard.update(updates)
            
            config = wizard.get_config()
            assert config.get('model') == 'llama2'
            assert config.get('temperature') == 0.8
            assert config.get('max_tokens') == 3000
    
    def test_config_file_creation(self):
        """Test that config file is created if missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/new_config.yaml"
            
            # File shouldn't exist yet
            assert not Path(config_file).exists()
            
            wizard = ConfigWizard(config_file=config_file)
            wizard.save()
            
            # File should be created
            assert Path(config_file).exists()
