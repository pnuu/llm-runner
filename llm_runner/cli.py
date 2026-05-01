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
        "mode_or_prompt",
        nargs="?",
        help="Either '/ask' for single prompt mode, or the prompt text"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The prompt text (when using /ask)"
    )
    parser.add_argument(
        "--model",
        help="Override model from config"
    )
    parser.add_argument(
        "--config",
        help="Path to config file"
    )
    
    parsed = parser.parse_args(args)
    
    # Determine mode and extract prompt if needed
    if parsed.mode_or_prompt == "/ask":
        parsed.mode = "ask"
        parsed.prompt = parsed.prompt or ""
    else:
        parsed.mode = "interactive"
        if parsed.mode_or_prompt:
            # If something else was passed, treat it as interactive mode
            parsed.prompt = None
        else:
            parsed.prompt = None
    
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
    
    if parsed.mode == "ask":
        send_prompt_mode(parsed.prompt, config=parsed.config, model=parsed.model)
    else:
        interactive_mode(config=parsed.config)
