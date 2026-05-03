"""Tests for bug fixes - model override and file writing"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from llm_runner.cli import parse_args, run_cli
from llm_runner.executor import write_file_tool
from llm_runner.build_handler import handle_build_mode


class TestModelOverride:
    """Test that --model flag overrides configured model"""
    
    def test_ask_mode_model_override(self):
        """Test --model overrides configured model in ask mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump({"model": "configured-model"}, f)
            
            # Parse args with model override
            args = ["--config", config_file, "--model", "override-model", "/ask", "test prompt"]
            parsed = parse_args(args)
            
            assert parsed.model == "override-model"
    
    def test_plan_mode_model_override(self):
        """Test --model overrides in plan mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump({"model": "configured-model"}, f)
            
            args = ["--config", config_file, "--model", "override-model", "plan", "test"]
            parsed = parse_args(args)
            
            assert parsed.model == "override-model"
    
    def test_build_mode_model_override(self):
        """Test --model overrides in build mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump({"model": "configured-model"}, f)
            
            args = ["--config", config_file, "--model", "override-model", "build", "test"]
            parsed = parse_args(args)
            
            assert parsed.model == "override-model"
    
    def test_interactive_mode_model_override(self):
        """Test --model flag passed to interactive mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.yaml"
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump({"model": "configured-model"}, f)
            
            args = ["--config", config_file, "--model", "override-model"]
            parsed = parse_args(args)
            
            # Parse should recognize the model override even in interactive mode
            assert parsed.model == "override-model"


class TestFileWriting:
    """Test that build mode actually writes files to disk"""
    
    def test_write_file_tool_creates_file(self):
        """Test write_file_tool actually writes to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!"
            
            result = write_file_tool(filepath, content)
            
            # Verify file was written
            assert Path(filepath).exists()
            assert Path(filepath).read_text() == content
            assert "Wrote to file" in result
    
    def test_write_file_tool_creates_directories(self):
        """Test write_file_tool creates missing directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "nested", "file.txt")
            content = "Nested content"
            
            result = write_file_tool(filepath, content)
            
            assert Path(filepath).exists()
            assert Path(filepath).read_text() == content
    
    def test_hello_world_c_file(self):
        """Test creating hello.c file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            c_code = '''#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
'''
            filepath = os.path.join(tmpdir, "hello.c")
            result = write_file_tool(filepath, c_code)
            
            assert Path(filepath).exists()
            assert "hello.c" in result
            content = Path(filepath).read_text()
            assert "printf" in content
            assert "Hello, World!" in content
