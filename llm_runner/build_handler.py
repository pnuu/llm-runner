"""Handler for build mode"""
import os
from llm_runner.executor import BuildExecutor
from llm_runner.llm import OllamaClient, check_ollama_connection
from llm_runner.plan_handler import read_agents_context


def handle_build_mode(request, workspace_dir=".", config=None, use_context=False):
    """Handle build mode request
    
    Args:
        request: User's build request
        workspace_dir: Workspace directory for file operations
        config: Configuration dict
        use_context: Whether to include AGENTS.md context
        
    Returns:
        Executor summary or None if error
    """
    # Load config if not provided
    if config is None:
        from llm_runner.config import load_config
        config = load_config()
    
    try:
        # Extract config values
        ollama_url = config.get("ollama_url", "http://localhost:11434")
        model = config.get("model", "mistral:7b")
        temperature = config.get("temperature", 0.7)
        
        # Check connection
        if not check_ollama_connection(ollama_url):
            print(f"Error: Cannot connect to Ollama at {ollama_url}")
            return None
        
        # Get context if requested
        context = None
        if use_context:
            context = read_agents_context(workspace_dir)
        
        # Create executor
        print(f"Initializing build executor in: {workspace_dir}")
        executor = BuildExecutor(workspace_dir=workspace_dir)
        
        # Create client
        client = OllamaClient(url=ollama_url)
        
        # Build prompt for build request
        prompt = _build_prompt(request, executor, context)
        
        print(f"Planning build for: {request}")
        
        # Get response from LLM
        response = client.send_prompt(
            prompt,
            model=model,
            temperature=temperature
        )
        
        # For now, just print the response
        print(f"\nBuild Plan:\n{response}\n")
        
        # Get summary
        summary = executor.get_summary()
        print(summary)
        
        return summary
        
    except Exception as e:
        print(f"✗ Error in build mode: {e}")
        return None


def _build_prompt(request, executor, context=None):
    """Build the build mode prompt
    
    Args:
        request: User request
        executor: BuildExecutor instance
        context: Optional context
        
    Returns:
        Formatted prompt
    """
    prompt = f"""You are a build assistant. Based on the user's request, provide a detailed build plan.

Request: {request}

Available tools you can suggest:
- create_file(path, content) - Create a new file
- write_file(path, content) - Write/overwrite a file
- read_file(path) - Read a file
- run_command(cmd) - Run a shell command

"""
    
    if context:
        prompt += f"Context/Guidelines:\n{context}\n\n"
    
    prompt += """Provide a step-by-step plan that includes:
1. What files to create
2. What commands to run
3. Any necessary setup

Be specific about file paths and content."""
    
    return prompt
