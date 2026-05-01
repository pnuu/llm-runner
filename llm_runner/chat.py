"""Interactive chat module"""
from llm_runner.llm import OllamaClient, check_ollama_connection


class ConversationHistory:
    """Manages conversation history"""
    
    def __init__(self):
        """Initialize empty conversation"""
        self.messages = []
    
    def add_user_message(self, content):
        """Add user message to history
        
        Args:
            content: User message text
        """
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content):
        """Add assistant message to history
        
        Args:
            content: Assistant response text
        """
        self.messages.append({"role": "assistant", "content": content})
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
    
    def get_context(self):
        """Get formatted context for LLM
        
        Returns:
            Formatted conversation history
        """
        context = ""
        for msg in self.messages:
            role = msg["role"].capitalize()
            context += f"{role}: {msg['content']}\n"
        return context


class InteractiveChat:
    """Interactive chat session with Ollama"""
    
    def __init__(self, ollama_url="http://localhost:11434", model="mistral", temperature=0.7):
        """Initialize interactive chat
        
        Args:
            ollama_url: Ollama API endpoint
            model: Model to use
            temperature: Temperature for responses
            
        Raises:
            Exception: If Ollama is not accessible
        """
        # Check connection first
        if not check_ollama_connection(ollama_url):
            raise Exception(f"Cannot connect to Ollama at {ollama_url}")
        
        self.client = OllamaClient(url=ollama_url)
        self.model = model
        self.temperature = temperature
        self.history = ConversationHistory()
    
    def process_input(self, user_input):
        """Process user input, handling commands
        
        Args:
            user_input: User input string
            
        Returns:
            "quit" if /quit was entered, None otherwise
        """
        if user_input.startswith("/"):
            command = user_input.lower().strip()
            
            if command == "/quit":
                return "quit"
            elif command == "/clear":
                self.history.clear()
                return None
            else:
                # Unknown command
                return None
        
        return None
    
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
            temperature=config.get("temperature", 0.7)
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
    print("Type '/quit' to exit, '/clear' to clear history")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for commands
            command_result = chat.process_input(user_input)
            if command_result == "quit":
                print("Goodbye!")
                break
            elif user_input.startswith("/"):
                # Command was processed but not quit/clear
                continue
            
            # Send message to LLM
            response = chat.send_message(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
