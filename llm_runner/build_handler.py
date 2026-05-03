"""Handler for build mode"""
import os
import re
from llm_runner.executor import BuildExecutor
from llm_runner.llm import OllamaClient, check_ollama_connection
from llm_runner.plan_handler import read_agents_context


def _execute_suggested_tools(response, executor):
    """Parse LLM response and execute suggested tools
    
    Args:
        response: LLM response text
        executor: BuildExecutor instance to use for tool execution
    """
    # Pattern to match write_file(path, content) calls
    write_pattern = r'write_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^)]+)\)'
    
    matches = re.finditer(write_pattern, response, re.IGNORECASE)
    for match in matches:
        filepath = match.group(1)
        content_expr = match.group(2)
        
        # Try to extract content - handle various formats
        if content_expr.startswith('[') or content_expr.startswith('{'):
            # Skip complex expressions for now
            continue
        
        # Remove quotes if present
        content = content_expr.strip().strip('"\'')
        
        # Execute the write_file tool
        try:
            result = executor.run_tool("write_file", filepath, content)
            print(f"  ✓ {result}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Pattern to match code blocks that should be written (markdown code fences)
    code_block_pattern = r'```\w+\n([\s\S]*?)```'
    
    # Look for patterns like "create file: hello.c" followed by code
    file_pattern = r'(?:create|write|save)\s+(?:file|code)\s*:?\s*["\']?([^\s"\']+)["\']?'
    
    # Try to match file creation patterns with following code blocks
    lines = response.split('\n')
    i = 0
    while i < len(lines):
        # Check if line mentions creating a file
        file_match = re.search(file_pattern, lines[i], re.IGNORECASE)
        if file_match:
            filepath = file_match.group(1)
            
            # Look for code block in next few lines
            j = i + 1
            while j < min(i + 10, len(lines)):
                if lines[j].strip().startswith('```'):
                    # Found code block, collect until closing ```
                    code_lines = []
                    j += 1
                    while j < len(lines) and not lines[j].strip().startswith('```'):
                        code_lines.append(lines[j])
                        j += 1
                    
                    if code_lines:
                        content = '\n'.join(code_lines)
                        try:
                            result = executor.run_tool("write_file", filepath, content)
                            print(f"  ✓ {result}")
                        except Exception as e:
                            print(f"  ✗ Error: {e}")
                    break
                j += 1
        
        i += 1


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
        
        print(f"\nBuild Plan:\n{response}\n")
        
        # Execute suggested tools from the response
        print("Executing build tools...\n")
        _execute_suggested_tools(response, executor)
        
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
