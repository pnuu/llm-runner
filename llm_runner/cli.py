"""CLI module for argument parsing and command routing"""
import argparse


def parse_args(args):
    """Parse command line arguments
    
    Args:
        args: List of command line arguments
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Chat with local LLMs via Ollama"
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="Command: 'plan', 'build', '/ask', or empty for interactive"
    )
    parser.add_argument(
        "request_or_prompt",
        nargs="?",
        help="Request text for plan/build, or prompt text for /ask"
    )
    parser.add_argument(
        "--model",
        help="Override model from config"
    )
    parser.add_argument(
        "--config",
        help="Path to config file"
    )
    parser.add_argument(
        "--context",
        action="store_true",
        help="Include AGENTS.md context in plan/build"
    )
    
    parsed = parser.parse_args(args)
    
    # Determine mode
    if parsed.command == "plan":
        parsed.mode = "plan"
        parsed.request = parsed.request_or_prompt or ""
    elif parsed.command == "build":
        parsed.mode = "build"
        parsed.request = parsed.request_or_prompt or ""
    elif parsed.command == "/ask":
        parsed.mode = "ask"
        parsed.prompt = parsed.request_or_prompt or ""
    else:
        parsed.mode = "interactive"
        parsed.prompt = None
        parsed.request = None
    
    return parsed


def send_prompt_mode(prompt, config=None, model=None):
    """Execute single prompt mode
    
    Args:
        prompt: The prompt text
        config: Configuration dict or path
        model: Optional model override
    """
    from llm_runner.config import load_config
    from llm_runner.llm import OllamaClient, check_ollama_connection
    
    # Load config
    if config is None or isinstance(config, str):
        cfg = load_config(config)
    else:
        cfg = config
    
    # Override model if specified
    if model:
        cfg["model"] = model
    
    # Check connection
    url = cfg.get("ollama_url", "http://localhost:11434")
    if not check_ollama_connection(url):
        print(f"Error: Cannot connect to Ollama at {url}")
        return
    
    # Send prompt and get response
    client = OllamaClient(url=url)
    response = client.send_prompt(
        prompt,
        model=cfg.get("model", "mistral"),
        temperature=cfg.get("temperature", 0.7)
    )
    
    print(response)


def plan_mode(request, config=None, model=None, use_context=False):
    """Execute plan mode
    
    Args:
        request: The user request
        config: Configuration dict or path
        model: Optional model override
        use_context: Whether to use AGENTS.md context
    """
    from llm_runner.config import load_config
    from llm_runner.plan_handler import handle_plan_mode
    
    # Load config
    if config is None or isinstance(config, str):
        cfg = load_config(config)
    else:
        cfg = config
    
    # Override model if specified
    if model:
        cfg["model"] = model
    
    # Handle plan mode
    handle_plan_mode(request, output_dir=".", config=cfg, use_context=use_context)


def build_mode(request, config=None, model=None, use_context=False):
    """Execute build mode
    
    Args:
        request: The user request
        config: Configuration dict or path
        model: Optional model override
        use_context: Whether to use AGENTS.md context
    """
    # Stub for now - will implement in next todo
    print(f"Build mode: {request}")


def interactive_mode(config=None):
    """Execute interactive chat mode
    
    Args:
        config: Configuration dict or path
    """
    from llm_runner.config import load_config
    from llm_runner.chat import interactive_chat_repl
    
    # Load config
    if config is None or isinstance(config, str):
        cfg = load_config(config)
    else:
        cfg = config
    
    interactive_chat_repl(cfg)


def run_cli(args):
    """Main CLI entry point
    
    Args:
        args: List of command line arguments
    """
    parsed = parse_args(args)
    
    if parsed.mode == "plan":
        plan_mode(
            parsed.request,
            config=parsed.config,
            model=parsed.model,
            use_context=getattr(parsed, "context", False)
        )
    elif parsed.mode == "build":
        build_mode(
            parsed.request,
            config=parsed.config,
            model=parsed.model,
            use_context=getattr(parsed, "context", False)
        )
    elif parsed.mode == "ask":
        send_prompt_mode(parsed.prompt, config=parsed.config, model=parsed.model)
    else:
        interactive_mode(config=parsed.config)
