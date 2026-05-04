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
    processed_files = set()
    
    # First: Handle write_file("path", content) direct function calls
    write_pattern = r'write_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^)]+)\)'
    matches = re.finditer(write_pattern, response, re.IGNORECASE)
    for match in matches:
        filepath = match.group(1)
        content_expr = match.group(2)
        
        # Skip complex expressions (variables, function calls)
        if content_expr.startswith('[') or content_expr.startswith('{') or 'content' in content_expr.lower():
            continue
        
        # Remove quotes if present
        content = content_expr.strip().strip('"\'')
        
        # Unescape common escape sequences
        content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        
        # Execute the write_file tool
        try:
            result = executor.execute_tool("write_file", [filepath, content])
            print(f"  ✓ {result}")
            processed_files.add(filepath)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Second: Look for patterns like "create file: hello.c", "**File: hello.c**", or "Create the `hello.c`"
    # followed by code blocks. More robust filename extraction.
    file_patterns = [
        # Match: **File: hello.c** or **file: hello.c**
        r'\*\*(?:file|File)\s*:\s*([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)\*\*',
        # Match: Create/Write/Save ... `hello.c` or "hello.c" or hello.c
        r'(?:create|write|save).*?\s+(?:the\s+)?[`"\']?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)[`"\']?',
        # Match: File: hello.c at line start
        r'^File\s*:\s*([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)',
    ]
    
    # Try to match file creation patterns with following code blocks
    lines = response.split('\n')
    i = 0
    
    # Also look for code blocks that mention a filename nearby
    code_block_pattern = r'save.*?(?:to|as|named)\s+[`"\']?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)[`"\']?'
    
    while i < len(lines):
        # Try each pattern
        filepath = None
        for file_pattern in file_patterns:
            file_match = re.search(file_pattern, lines[i], re.IGNORECASE)
            if file_match:
                filepath = file_match.group(1)
                # Skip if we already processed this file
                if filepath not in processed_files:
                    break
                filepath = None
        
        if filepath:
            # Look for code block in next few lines
            j = i + 1
            found_code = False
            while j < min(i + 15, len(lines)) and not found_code:
                if lines[j].strip().startswith('```'):
                    # Found code block, check language identifier
                    language = lines[j].strip()[3:].strip().lower()
                    
                    # Skip bash/shell blocks - those are commands, not code to save
                    if language and language in ('bash', 'shell', 'sh', 'zsh', 'cmd', 'powershell'):
                        j += 1
                        # Skip to end of this code block
                        while j < len(lines) and not lines[j].strip().startswith('```'):
                            j += 1
                        j += 1
                        continue
                    
                    # Collect code from this block
                    code_lines = []
                    j += 1
                    # Skip language identifier if present
                    if j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('```'):
                        first_line = lines[j].strip()
                        # If it looks like a language identifier (short, lowercase), skip it
                        if len(first_line) < 20 and first_line.replace('+', '').replace('-', '').replace('#', '').isalnum():
                            j += 1
                        else:
                            code_lines.append(lines[j])
                            j += 1
                    
                    while j < len(lines) and not lines[j].strip().startswith('```'):
                        code_lines.append(lines[j])
                        j += 1
                    
                    if code_lines:
                        content = '\n'.join(code_lines).rstrip()
                        try:
                            result = executor.execute_tool("write_file", [filepath, content])
                            print(f"  ✓ {result}")
                            processed_files.add(filepath)
                            found_code = True
                        except Exception as e:
                            print(f"  ✗ Error: {e}")
                    break
                j += 1
        
        # Third: Look for code blocks followed/preceded by filename mentions
        # This catches cases where LLM just shows code without explicit "create" language
        if i < len(lines) and lines[i].strip().startswith('```'):
            language = lines[i].strip()[3:].strip().lower()
            
            # Skip bash/shell blocks
            if language and language in ('bash', 'shell', 'sh', 'zsh', 'cmd', 'powershell'):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    i += 1
                i += 1
                continue
            
            # Check if this code block is preceded or followed by a mention of a filename
            filename_from_context = None
            if language and language in ('c', 'cpp', 'h', 'cc', 'cxx', 'js', 'py', 'java', 'go', 'rust', 'rb', 'php', 'ts', 'jsx', 'tsx'):
                # Look back up to 5 lines for filename mentions
                for look_back in range(1, min(6, i + 1)):
                    prev_line = lines[i - look_back].lower()
                    # Look for patterns like "to hello.c", "named hello.c", "file hello.c"
                    for pattern in [r'(?:to|as|named|file)\s+[`"\']?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)[`"\']?']:
                        m = re.search(pattern, prev_line)
                        if m:
                            candidate = m.group(1)
                            if candidate not in processed_files:
                                filename_from_context = candidate
                                break
                    if filename_from_context:
                        break
                
                # If not found before, look ahead up to 10 lines for filename mentions
                if not filename_from_context:
                    j = i + 1
                    # Skip to end of code block first
                    while j < len(lines) and not lines[j].strip().startswith('```'):
                        j += 1
                    j += 1  # Move past closing ```
                    
                    # Now look ahead
                    for look_ahead_dist in range(0, min(8, len(lines) - j)):
                        next_line = lines[j + look_ahead_dist].lower()
                        for pattern in [r'(?:to|as|named|file|save.*?as)\s+[`"\']?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)[`"\']?']:
                            m = re.search(pattern, next_line)
                            if m:
                                candidate = m.group(1)
                                if candidate not in processed_files:
                                    filename_from_context = candidate
                                    break
                        if filename_from_context:
                            break
            
            if filename_from_context:
                # Collect code from this block
                code_lines = []
                j = i + 1
                # Skip language identifier
                if j < len(lines) and lines[j].strip():
                    first_line = lines[j].strip()
                    if len(first_line) < 20 and first_line.replace('+', '').replace('-', '').replace('#', '').isalnum():
                        j += 1
                    else:
                        code_lines.append(lines[j])
                        j += 1
                
                while j < len(lines) and not lines[j].strip().startswith('```'):
                    code_lines.append(lines[j])
                    j += 1
                
                if code_lines:
                    content = '\n'.join(code_lines).rstrip()
                    try:
                        result = executor.execute_tool("write_file", [filename_from_context, content])
                        print(f"  ✓ {result}")
                        processed_files.add(filename_from_context)
                    except Exception as e:
                        print(f"  ✗ Error: {e}")
        
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
