"""Test CLI module"""
import sys
from unittest.mock import patch
import pytest
from llm_runner.cli import parse_args, run_cli


def test_parse_args_ask_mode():
    """Test parsing /ask command"""
    args = parse_args(["/ask", "Hello world"])
    assert args.mode == "ask"
    assert args.prompt == "Hello world"


def test_parse_args_ask_with_model():
    """Test parsing /ask with model override"""
    args = parse_args(["/ask", "Hello", "--model", "neural-chat"])
    assert args.mode == "ask"
    assert args.prompt == "Hello"
    assert args.model == "neural-chat"


def test_parse_args_interactive_mode():
    """Test interactive mode (no arguments)"""
    args = parse_args([])
    assert args.mode == "interactive"


def test_parse_args_with_config_file():
    """Test specifying custom config file"""
    args = parse_args(["--config", "/tmp/custom.yaml"])
    assert args.config == "/tmp/custom.yaml"


def test_run_cli_ask_mode():
    """Test CLI execution in ask mode"""
    with patch("llm_runner.cli.send_prompt_mode") as mock_send:
        mock_send.return_value = None
        
        run_cli(["/ask", "test prompt"])
        
        mock_send.assert_called_once()


def test_run_cli_interactive_mode():
    """Test CLI execution in interactive mode"""
    with patch("llm_runner.cli.interactive_mode") as mock_interactive:
        mock_interactive.return_value = None
        
        run_cli([])
        
        mock_interactive.assert_called_once()
