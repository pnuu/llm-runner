"""Interactive chat module"""
from llm_runner.llm import OllamaClient, check_ollama_connection, get_available_models
from llm_runner.context_manager import ContextManager
from llm_runner.ui_formatter import ChatUIFormatter
from llm_runner.config import get_chat_colors


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
    
    def __init__(self, ollama_url="http://localhost:11434", model="mistral", temperature=0.7, max_context_tokens=4096, timeout_enabled=True):
        """Initialize interactive chat
        
        Args:
            ollama_url: Ollama API endpoint
            model: Model to use
            temperature: Temperature for responses
            max_context_tokens: Maximum tokens before compaction recommended
            timeout_enabled: Whether to enforce timeouts (default True)
            
        Raises:
            Exception: If Ollama is not accessible
        """
        # Check connection first
        if not check_ollama_connection(ollama_url):
            raise Exception(f"Cannot connect to Ollama at {ollama_url}")
        
        self.client = OllamaClient(url=ollama_url, timeout_enabled=timeout_enabled)
        self.model = model
        self.temperature = temperature
        self.history = ConversationHistory(max_tokens=max_context_tokens)
        self.auto_compact_enabled = True
        self.auto_compact_threshold_percent = 90
        self.plan_mode_state = None  # Track state when in plan refinement mode
        self.timeout_enabled = timeout_enabled
    
    def process_input(self, user_input):
        """Process user input, handling commands
        
        Args:
            user_input: User input string
            
        Returns:
            Tuple of (command_result, output) or (None, None) for regular input
        """
        if user_input.startswith("/"):
            command = user_input.lower().strip()
            
            # When executing any command other than /plan, exit plan mode first
            if self.plan_mode_state and command != "/plan":
                self.exit_plan_mode()
            
            if command == "/quit":
                return ("quit", None)
            elif command == "/clear":
                self.history.clear()
                return ("clear", "Conversation history cleared.")
            elif command == "/context":
                return ("context", self._get_context_display())
            elif command == "/model":
                return self._handle_model_command()
            elif command == "/plan":
                return self._handle_plan_command()
            elif command == "/build":
                return self._handle_build_command()
            elif command == "/ask":
                return self._handle_ask_command()
            elif command.startswith("/timeout"):
                return self._handle_timeout_command(user_input)
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
        display.append("")
        display.append("=== Timeout ===")
        timeout_state = "ENABLED" if self.timeout_enabled else "DISABLED"
        display.append(f"Timeout enforcement: {timeout_state}")
        
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
    
    def _handle_model_command(self):
        """Handle /model command - interactive model selection
        
        Returns:
            Tuple of (command_result, output)
        """
        # Get list of available models
        url = self.client.url
        models = get_available_models(url)
        
        if not models:
            return ("model_command", "No models available.")
        
        # Display menu with current model highlighted
        print("\nAvailable models:")
        for i, model in enumerate(models, 1):
            marker = " ← current" if model == self.model else ""
            print(f"  {i}. {model}{marker}")
        
        try:
            selection = input("\nSelect model (number or Enter for current): ").strip()
            
            if not selection:
                return ("model_command", f"Using model: {self.model}")
            
            try:
                idx = int(selection) - 1
                if 0 <= idx < len(models):
                    new_model = models[idx]
                    self.model = new_model
                    return ("model_command", f"Switched to model: {new_model}")
                else:
                    return ("model_command", "Invalid selection.")
            except ValueError:
                return ("model_command", "Invalid input. Using current model.")
        except (KeyboardInterrupt, EOFError):
            return ("model_command", "Model selection cancelled.")
    
    def _handle_plan_command(self):
        """Handle /plan command - enter plan refinement mode
        
        This enters interactive plan refinement mode where:
        1. Existing plan.md is displayed as outline
        2. Plan content is added to conversation context
        3. Refinements are detected and saved on exit
        
        Returns:
            Tuple of (command_result, output)
        """
        try:
            from llm_runner.plan_handler import handle_interactive_plan_refinement
            
            # Enter plan refinement mode and setup context
            plan_state = handle_interactive_plan_refinement(output_dir=".")
            
            if not plan_state:
                return ("plan_command", "Error entering plan refinement mode.")
            
            # Store plan state for later refinement detection
            self.plan_mode_state = plan_state
            
            # Add plan to conversation context as system message
            if plan_state["has_existing_plan"] and plan_state["original_plan"]:
                # Add plan file as context
                plan_context = f"""[PLAN CONTEXT]
The following is the current plan file being refined:

{plan_state['original_plan']}
[END PLAN CONTEXT]"""
                
                self.history.add_user_message(plan_context)
            
            output = "Entered plan refinement mode. You can now discuss and refine the plan."
            return ("plan_command", output)
        
        except (KeyboardInterrupt, EOFError):
            self.plan_mode_state = None
            return ("plan_command", "Plan refinement mode cancelled.")
        except Exception as e:
            self.plan_mode_state = None
            return ("plan_command", f"Error in plan refinement mode: {e}")
    
    def exit_plan_mode(self):
        """Exit plan mode and detect/save refinements
        
        Should be called when transitioning out of plan mode to detect
        and save any refinements made to the plan during chat.
        
        Returns:
            True if plan was refined and saved, False otherwise
        """
        if not self.plan_mode_state:
            return False
        
        try:
            from llm_runner.plan_handler import detect_and_save_plan_refinement
            
            # Get full chat context
            chat_content = self.history.get_context()
            
            # Detect and save refinements
            was_refined = detect_and_save_plan_refinement(
                self.plan_mode_state,
                chat_content,
                output_dir="."
            )
            
            self.plan_mode_state = None
            return was_refined
        
        except Exception as e:
            print(f"Error exiting plan mode: {e}")
            self.plan_mode_state = None
            return False
    
    def _handle_build_command(self):
        """Handle /build command - switch to build mode
        
        Returns:
            Tuple of (command_result, output)
        """
        try:
            build_request = input("Enter build request: ").strip()
            
            if not build_request:
                return ("build_command", "No build request provided.")
            
            # Note: Actual build execution happens in main mode,
            # this just returns to chat after user inputs
            output = f"Build mode: '{build_request}' - complete in main mode for persistence"
            return ("build_command", output)
        except (KeyboardInterrupt, EOFError):
            return ("build_command", "Build mode cancelled.")
        except Exception as e:
            return ("build_command", f"Error in build mode: {e}")
    
    def _handle_ask_command(self):
        """Handle /ask command - context-aware single prompt
        
        Returns:
            Tuple of (command_result, output)
        """
        try:
            question = input("Ask (with context): ").strip()
            
            if not question:
                return ("ask_command", "No question provided.")
            
            # Get context and include it in the prompt
            context = self.history.get_context()
            
            # Send prompt with context (but don't store in history)
            prompt_with_context = f"{context}\n\nQ: {question}" if context else question
            response = self.client.send_prompt(
                prompt_with_context,
                model=self.model,
                temperature=self.temperature
            )
            
            # Important: Do NOT add to history
            output = f"[Not stored in history]\n{response}"
            return ("ask_command", output)
        except (KeyboardInterrupt, EOFError):
            return ("ask_command", "Ask command cancelled.")
        except Exception as e:
            return ("ask_command", f"Error in ask command: {e}")
    
    def _handle_timeout_command(self, user_input):
        """Handle /timeout command - toggle timeout enforcement
        
        Args:
            user_input: Raw user input (e.g., "/timeout off")
            
        Returns:
            Tuple of (command_result, output)
        """
        parts = user_input.lower().strip().split()
        
        if len(parts) < 2:
            return ("timeout", f"Usage: /timeout [on|off|status]. Current: {'Enabled' if self.timeout_enabled else 'Disabled'}")
        
        subcommand = parts[1].lower()
        
        if subcommand == "on":
            self.timeout_enabled = True
            self.client.timeout_enabled = True
            return ("timeout", "Timeout enforcement is now ENABLED.")
        elif subcommand == "off":
            self.timeout_enabled = False
            self.client.timeout_enabled = False
            return ("timeout", "Timeout enforcement is now DISABLED.")
        elif subcommand == "status":
            status = "ENABLED" if self.timeout_enabled else "DISABLED"
            return ("timeout", f"Timeout enforcement is currently {status}.")
        else:
            return ("timeout", f"Unknown timeout subcommand '{subcommand}'. Use: on, off, or status.")


def interactive_chat_repl(config=None, model=None, disable_timeout=False):
    """Run interactive REPL chat
    
    Args:
        config: Configuration dictionary
        model: Optional model override
        disable_timeout: If True, disable timeout enforcement
    """
    if config is None:
        from llm_runner.config import load_config
        config = load_config()
    
    # Override model if specified
    if model:
        config["model"] = model
    
    try:
        # Fetch actual context length from the model
        from llm_runner.llm import OllamaClient
        client = OllamaClient(url=config.get("ollama_url", "http://localhost:11434"))
        model_name = config.get("model", "mistral")
        max_context_tokens = client.get_model_context_length(model_name)
        
        # Store in config for later use
        config["max_context_tokens"] = max_context_tokens
        
        chat = InteractiveChat(
            ollama_url=config.get("ollama_url", "http://localhost:11434"),
            model=config.get("model", "mistral"),
            temperature=config.get("temperature", 0.7),
            max_context_tokens=max_context_tokens,
            timeout_enabled=not disable_timeout
        )
    except Exception as e:
        print(f"Error: {e}")
        return
    
    url = config.get("ollama_url", "http://localhost:11434")
    
    # Initialize UI formatter with color config
    color_config = get_chat_colors(config)
    formatter = ChatUIFormatter(color_config)
    
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
    print("Commands: '/quit' (exit), '/clear' (history), '/context' (info), '/model' (select),")
    print("          '/plan' (plan mode), '/build' (build mode), '/ask' (non-storing ask)")
    print()
    
    while True:
        try:
            # Get context percentage for status line
            context_info = chat.history.get_context_info()
            context_percent = context_info.get('percent_of_max', 0)
            
            # Show status line before input
            status = formatter.format_status_line(
                model=chat.model,
                mode="interactive",
                context_percent=context_percent
            )
            print(status)
            
            # Get user input with formatted prompt
            prompt = formatter.format_command_prompt()
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Check for commands
            command_result, output = chat.process_input(user_input)
            
            if command_result == "quit":
                # Exit plan mode if active before quitting
                if chat.plan_mode_state:
                    chat.exit_plan_mode()
                print("Goodbye!")
                break
            elif command_result == "clear":
                print(output)
                continue
            elif command_result == "context":
                print(f"\n{output}\n")
                continue
            elif command_result == "model_command":
                print(f"\n{output}\n")
                continue
            elif command_result == "plan_command":
                print(f"\n{output}\n")
                continue
            elif command_result == "build_command":
                print(f"\n{output}\n")
                continue
            elif command_result == "ask_command":
                print(f"\n{output}\n")
                continue
            elif command_result == "timeout":
                print(f"\n{output}\n")
                continue
            elif command_result == "unknown":
                # Unknown command
                continue
            
            # Send message to LLM
            response = chat.send_message(user_input)
            
            # Format and display response (no "Assistant:" label)
            formatted_response = formatter.format_ai_message(response)
            print(f"\n{formatted_response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
