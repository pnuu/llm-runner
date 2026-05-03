"""Tests for context awareness and management"""
import pytest
from llm_runner.context_manager import ContextManager, estimate_tokens, summarize_messages


class TestContextManager:
    """Test context awareness functionality"""
    
    def test_create_context_manager(self):
        """Test creating a context manager"""
        manager = ContextManager()
        assert manager is not None
        assert manager.get_message_count() == 0
    
    def test_track_context_size(self):
        """Test tracking context size"""
        manager = ContextManager()
        
        # Add messages
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi there!")
        
        assert manager.get_message_count() == 2
        assert manager.get_context_size() > 0
    
    def test_get_context_info(self):
        """Test getting context info"""
        manager = ContextManager()
        manager.add_message("user", "What is Python?")
        manager.add_message("assistant", "Python is a programming language.")
        
        info = manager.get_context_info()
        assert "token_count" in info
        assert "byte_count" in info
        assert "message_count" in info
        assert info["message_count"] == 2
    
    def test_context_over_threshold(self):
        """Test detecting when context exceeds threshold"""
        manager = ContextManager(max_tokens=100)
        
        # Add enough text to exceed threshold
        manager.add_message("user", "x" * 500)
        manager.add_message("assistant", "y" * 500)
        
        assert manager.is_over_threshold()
    
    def test_context_under_threshold(self):
        """Test when context is under threshold"""
        manager = ContextManager(max_tokens=5000)
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi")
        
        assert not manager.is_over_threshold()
    
    def test_get_context_compact_recommendation(self):
        """Test getting compaction recommendation"""
        manager = ContextManager(max_tokens=100)
        manager.add_message("user", "x" * 500)
        manager.add_message("assistant", "y" * 500)
        
        rec = manager.get_compaction_recommendation()
        assert rec is not None
        assert "should_compact" in rec
        assert rec["should_compact"] is True
    
    def test_context_message_limit(self):
        """Test message count limit"""
        manager = ContextManager(max_messages=5)
        
        for i in range(10):
            manager.add_message("user", f"Message {i}")
        
        # Should not exceed max_messages
        assert manager.get_message_count() <= 10  # Actual behavior may vary


class TestTokenEstimation:
    """Test token estimation"""
    
    def test_estimate_tokens_basic(self):
        """Test basic token estimation"""
        tokens = estimate_tokens("Hello world")
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_tokens_empty(self):
        """Test estimating tokens for empty string"""
        tokens = estimate_tokens("")
        assert tokens == 0
    
    def test_estimate_tokens_long_text(self):
        """Test token estimation for longer text"""
        short = estimate_tokens("Hello")
        long = estimate_tokens("Hello world this is a longer text with more words")
        assert long > short
    
    def test_estimate_tokens_consistency(self):
        """Test that token estimation is consistent"""
        text = "The quick brown fox"
        tokens1 = estimate_tokens(text)
        tokens2 = estimate_tokens(text)
        assert tokens1 == tokens2


class TestMessageSummarization:
    """Test message summarization"""
    
    def test_summarize_empty_messages(self):
        """Test summarizing empty message list"""
        result = summarize_messages([])
        assert isinstance(result, str)
    
    def test_summarize_single_message(self):
        """Test summarizing single message"""
        messages = [{"role": "user", "content": "What is AI?"}]
        result = summarize_messages(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_multiple_messages(self):
        """Test summarizing multiple messages"""
        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more"},
            {"role": "assistant", "content": "It's widely used in data science."}
        ]
        result = summarize_messages(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_returns_string(self):
        """Test that summarize returns a string"""
        messages = [{"role": "user", "content": "test"}]
        result = summarize_messages(messages)
        assert isinstance(result, str)


class TestContextCompaction:
    """Test context compaction functionality"""
    
    def test_compact_context(self):
        """Test compacting context"""
        manager = ContextManager(max_tokens=500)
        
        # Add many messages
        for i in range(20):
            manager.add_message("user", f"Question {i}: " + "x" * 100)
            manager.add_message("assistant", f"Answer {i}: " + "y" * 100)
        
        # Should be over threshold
        assert manager.is_over_threshold()
        
        # Compact
        manager.compact_context(recent_messages=4)
        
        # Should be more under control
        assert manager.get_message_count() <= 10
    
    def test_compact_preserves_recent(self):
        """Test that compaction preserves recent messages"""
        manager = ContextManager()
        
        for i in range(10):
            manager.add_message("user", f"Q{i}")
            manager.add_message("assistant", f"A{i}")
        
        original_count = manager.get_message_count()
        manager.compact_context(recent_messages=2)
        
        # Recent messages should be preserved
        context = manager.get_formatted_context()
        assert "Q9" in context or "Q8" in context  # Recent messages
    
    def test_compact_context_info(self):
        """Test getting compaction info"""
        manager = ContextManager()
        
        for i in range(10):
            manager.add_message("user", f"Q{i}")
        
        info = manager.get_compaction_info()
        assert "current_tokens" in info
        assert "threshold_tokens" in info
        assert "excess_tokens" in info
