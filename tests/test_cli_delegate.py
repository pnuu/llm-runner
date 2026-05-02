"""Tests for delegate command CLI"""
import pytest
from llm_runner.cli import parse_args


class TestDelegateCommand:
    """Test delegate command parsing"""
    
    def test_delegate_command_parsing(self):
        """Test parsing delegate command"""
        args = parse_args(["delegate", "Create REST API"])
        
        assert args.command == "delegate"
        assert args.request == "Create REST API"
    
    def test_delegate_with_context_flag(self):
        """Test delegate with --context flag"""
        args = parse_args(["delegate", "Task", "--context"])
        
        assert args.command == "delegate"
        assert args.context is True
    
    def test_delegate_with_model_override(self):
        """Test delegate with --model override"""
        args = parse_args(["delegate", "Task", "--model", "neural-chat"])
        
        assert args.model == "neural-chat"
    
    def test_delegate_without_request(self):
        """Test delegate without request (empty string)"""
        args = parse_args(["delegate"])
        
        assert args.command == "delegate"
        assert args.request == ""
    
    def test_delegate_with_all_flags(self):
        """Test delegate with multiple flags"""
        args = parse_args([
            "delegate",
            "Complex task",
            "--context",
            "--model", "mistral:7b"
        ])
        
        assert args.command == "delegate"
        assert args.context is True
        assert args.model == "mistral:7b"
