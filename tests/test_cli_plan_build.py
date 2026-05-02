"""Test CLI plan and build modes"""
import sys
from unittest.mock import patch, MagicMock
import pytest
from llm_runner.cli import parse_args


def test_parse_args_plan_mode():
    """Test parsing plan command"""
    args = parse_args(["plan", "Create a REST API"])
    assert args.mode == "plan"
    assert args.request == "Create a REST API"


def test_parse_args_build_mode():
    """Test parsing build command"""
    args = parse_args(["build", "Add user authentication"])
    assert args.mode == "build"
    assert args.request == "Add user authentication"


def test_parse_args_plan_with_model():
    """Test plan mode with model override"""
    args = parse_args(["plan", "Create docs", "--model", "neural-chat"])
    assert args.mode == "plan"
    assert args.request == "Create docs"
    assert args.model == "neural-chat"


def test_parse_args_build_with_model():
    """Test build mode with model override"""
    args = parse_args(["build", "Fix bug", "--model", "mistral:7b"])
    assert args.mode == "build"
    assert args.request == "Fix bug"
    assert args.model == "mistral:7b"


def test_parse_args_plan_with_config():
    """Test plan mode with custom config"""
    args = parse_args(["plan", "Request", "--config", "/tmp/config.yaml"])
    assert args.config == "/tmp/config.yaml"


def test_parse_args_interactive_still_works():
    """Test that interactive mode still works after adding plan/build"""
    args = parse_args([])
    assert args.mode == "interactive"


def test_parse_args_ask_still_works():
    """Test that /ask mode still works"""
    args = parse_args(["/ask", "Hello"])
    assert args.mode == "ask"
    assert args.prompt == "Hello"
