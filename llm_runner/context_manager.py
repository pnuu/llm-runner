"""Context awareness and management module"""
import re
from typing import List, Dict, Any, Optional


def estimate_tokens(text: str) -> int:
    """Estimate token count using simple algorithm
    
    Approximate: ~4 characters per token on average
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Simple heuristic: split on whitespace and punctuation
    words = re.findall(r'\S+', text)
    # Average: ~4 chars per token
    total_chars = len(text)
    return max(len(words), total_chars // 4)


def summarize_messages(messages: List[Dict[str, str]]) -> str:
    """Create a summary of messages
    
    Args:
        messages: List of message dicts with "role" and "content"
        
    Returns:
        Summary string
    """
    if not messages:
        return "[No messages to summarize]"
    
    summary_parts = []
    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")[:100]  # Truncate for summary
        summary_parts.append(f"{role}: {content}")
    
    return "\n".join(summary_parts)


class ContextManager:
    """Manages context awareness and compaction"""
    
    def __init__(self, max_tokens: int = 4096, max_messages: int = 100):
        """Initialize context manager
        
        Args:
            max_tokens: Maximum token threshold before compaction recommended
            max_messages: Maximum messages to keep in context
        """
        self.messages = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.compact_summary = None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to context
        
        Args:
            role: "user" or "assistant"
            content: Message content
        """
        self.messages.append({"role": role, "content": content})
    
    def get_message_count(self) -> int:
        """Get current message count
        
        Returns:
            Number of messages
        """
        return len(self.messages)
    
    def get_context_size(self) -> int:
        """Get current context size in bytes
        
        Returns:
            Approximate byte count
        """
        return sum(len(msg.get("content", "")) for msg in self.messages)
    
    def get_token_count(self) -> int:
        """Get estimated token count
        
        Returns:
            Estimated token count
        """
        context = self.get_formatted_context()
        return estimate_tokens(context)
    
    def get_formatted_context(self) -> str:
        """Get formatted context for LLM
        
        Returns:
            Formatted conversation
        """
        if self.compact_summary and len(self.messages) > 5:
            # Include summary for old messages
            context = f"[Previous conversation summary]\n{self.compact_summary}\n\n"
        else:
            context = ""
        
        for msg in self.messages:
            role = msg["role"].capitalize()
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def is_over_threshold(self) -> bool:
        """Check if context exceeds token threshold
        
        Returns:
            True if over threshold
        """
        return self.get_token_count() > self.max_tokens
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get context information
        
        Returns:
            Dictionary with context stats
        """
        token_count = self.get_token_count()
        return {
            "message_count": self.get_message_count(),
            "token_count": token_count,
            "byte_count": self.get_context_size(),
            "max_tokens": self.max_tokens,
            "over_threshold": self.is_over_threshold(),
            "percent_of_max": int((token_count / self.max_tokens) * 100)
        }
    
    def get_compaction_recommendation(self) -> Dict[str, Any]:
        """Get recommendation for context compaction
        
        Returns:
            Dictionary with compaction recommendation
        """
        info = self.get_context_info()
        excess = info["token_count"] - self.max_tokens
        
        return {
            "should_compact": self.is_over_threshold(),
            "excess_tokens": max(0, excess),
            "messages_to_compact": max(0, self.get_message_count() - 4),
            "recommended_keep_recent": 4
        }
    
    def get_compaction_info(self) -> Dict[str, Any]:
        """Get detailed compaction information
        
        Returns:
            Dictionary with compaction details
        """
        current_tokens = self.get_token_count()
        excess = max(0, current_tokens - self.max_tokens)
        
        return {
            "current_tokens": current_tokens,
            "threshold_tokens": self.max_tokens,
            "excess_tokens": excess,
            "message_count": self.get_message_count(),
            "can_compact": self.get_message_count() > 4
        }
    
    def compact_context(self, recent_messages: int = 4, summarize_func=None) -> None:
        """Compact context by summarizing old messages
        
        Keeps recent messages verbatim, summarizes older ones
        
        Args:
            recent_messages: Number of recent messages to keep
            summarize_func: Optional custom summarization function
        """
        if len(self.messages) <= recent_messages:
            return
        
        # Split into old and recent
        old_messages = self.messages[:-recent_messages]
        recent = self.messages[-recent_messages:]
        
        # Summarize old messages
        if summarize_func:
            summary = summarize_func(old_messages)
        else:
            summary = summarize_messages(old_messages)
        
        # Store summary and keep recent
        self.compact_summary = summary
        self.messages = recent
    
    def clear(self) -> None:
        """Clear all messages and summary"""
        self.messages = []
        self.compact_summary = None
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()
