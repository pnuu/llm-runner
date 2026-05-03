"""Interactive chat module"""
from llm_runner.llm import OllamaClient, check_ollama_connection
from llm_runner.context_manager import ContextManager


class ConversationHistory:
    """Manages conversation history with context awareness"""
    
    def __init__(self, max_tokens=4096):
        """Initialize empty conversation
        
        Args:
            max_tokens: Maximum tokens before compaction recommended
        """
        self.context_manager = ContextManager(max_tokens=max_tokens)
    
    def add_user_message(self, content):
        """Add user message to history
        
        Args:
            content: User message text
        """
        self.context_manager.add_message("user", content)
    
    def add_assistant_message(self, content):
        """Add assistant message to history
        
        Args:
            content: Assistant response text
        """
        self.context_manager.add_message("assistant", content)
    
    def clear(self):
        """Clear conversation history"""
        self.context_manager.clear()
    
    @property
    def messages(self):
        """Get messages for compatibility"""
        return self.context_manager.get_messages()
    
    def get_context(self):
        """Get formatted context for LLM
        
        Returns:
            Formatted conversation history
        """
        return self.context_manager.get_formatted_context()
    
    def get_context_info(self):
        """Get context information
        
        Returns:
            Dictionary with context stats
        """
        return self.context_manager.get_context_info()
    
    def is_over_threshold(self):
        """Check if context exceeds token threshold
        
        Returns:
            True if over threshold
        """
        return self.context_manager.is_over_threshold()
    
    def compact_context(self, recent_messages=4):
        """Compact context by summarizing old messages
        
        Args:
            recent_messages: Number of recent messages to keep
        """
        self.context_manager.compact_context(recent_messages)


class InteractiveChat:
    """Interactive chat session with Ollama"""
    
    def __init__(self, ollama_url="http://localhost:11434", model="mistral", temperature=0.7, max_context_tokens=4096):
        """Initialize interactive chat
        
        Args:
            ollama_url: Ollama API endpoint
            model: Model to use
            temperature: Temperature for responses
            max_context_tokens: Maximum tokens before compaction recommended
            
        Raises:
            Exception: If Ollama is not accessible
        """
        # Check connection first
        if not check_ollama_connection(ollama_url):
            raise Exception(f"Cannot connect to Ollama at {ollama_url}")
        
        self.client = OllamaClient(url=ollama_url)
        self.model = model
        self.temperature = temperature
        self.history = ConversationHistory(max_tokens=max_context_tokens)
        self.auto_compact_enabled = True
        self.auto_compact_threshold_percent = 90
    
    def process_input(self, user_input):
        """Process user input, handling commands
        
        Args:
            user_input: User input string
            
        Returns:
            Tuple of (command_result, output) or (None, None) for regular input
        """
        if user_input.startswith("/"):
            command = user_input.lower().strip()
            
            if command == "/quit":
                return ("quit", None)
            elif command == "/clear":
                self.history.clear()
                return ("clear", "Conversation history cleared.")
            elif command == "/context":
                return ("context", self._get_context_display())
            else:
                # Unknown command
                return ("unknown", None)
        
        return (None, None)
    
    def _get_context_display(self):
        """Get formatted context information display
        
        Returns:
            Formatted string with context info
        """
        info = self.history.get_context_info()
        compaction = self.history.context_manager.get_compaction_recommendation()
        
        display = []
        display.append("=== Context Usage ===")
        display.append(f"Messages: {info['message_count']}")
        display.append(f"Tokens: {info['token_count']} / {info['max_tokens']}")
        display.append(f"Bytes: {info['byte_count']:,}")
        display.append(f"Usage: {info['percent_of_max']}%")
        
        if compaction["should_compact"]:
            display.append("")
            display.append("⚠️  Context Over Threshold")
            display.append(f"Excess tokens: {compaction['excess_tokens']}")
            display.append("Recommendation: Compact context or start new session")
            display.append("Use /clear to reset conversation")
        else:
            display.append("")
            display.append("✓ Context usage normal")
        
        return "\n".join(display)
    
    def _auto_compact_if_needed(self):
        """Automatically compact context if threshold exceeded"""
        if not self.auto_compact_enabled:
            return
        
        info = self.history.get_context_info()
        if info["percent_of_max"] >= self.auto_compact_threshold_percent:
            self.history.compact_context(recent_messages=4)
    
    def send_message(self, user_message):
        """Send a message and get response
        
        Args:
            user_message: User message text
            
        Returns:
            Assistant response text
        """
        # Add user message to history
        self.history.add_user_message(user_message)
        
        # Get response from model
        response = self.client.send_prompt(
            user_message,
            model=self.model,
            temperature=self.temperature
        )
        
        # Add response to history
        self.history.add_assistant_message(response)
        
        # Auto-compact if needed
        self._auto_compact_if_needed()
        
        return response


def interactive_chat_repl(config=None):
    """Run interactive REPL chat
    
    Args:
        config: Configuration dictionary
    """
    if config is None:
        from llm_runner.config import load_config
        config = load_config()
    
    try:
        chat = InteractiveChat(
            ollama_url=config.get("ollama_url", "http://localhost:11434"),
            model=config.get("model", "mistral"),
            temperature=config.get("temperature", 0.7),
            max_context_tokens=config.get("max_context_tokens", 4096)
        )
    except Exception as e:
        print(f"Error: {e}")
        return
    
    url = config.get("ollama_url", "http://localhost:11434")
    
    # Show available models if default isn't found
    from llm_runner.llm import get_available_models
    available = get_available_models(url)
    
    print(f"Connected to Ollama at {url}")
    if available:
        print(f"Available models: {', '.join(available)}")
    print(f"Using model: {chat.model}")
    if chat.model not in available and available:
        print(f"⚠️  Warning: '{chat.model}' not found in available models!")
        print(f"   Try: llm-runner --model {available[0]}")
    print("Type '/quit' to exit, '/clear' to clear history, '/context' to see context info")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for commands
            command_result, output = chat.process_input(user_input)
            
            if command_result == "quit":
                print("Goodbye!")
                break
            elif command_result == "clear":
                print(output)
                continue
            elif command_result == "context":
                print(f"\n{output}\n")
                continue
            elif command_result == "unknown":
                # Unknown command
                continue
            
            # Send message to LLM
            response = chat.send_message(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
