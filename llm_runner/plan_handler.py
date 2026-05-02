"""Handler for plan mode"""
import os
from llm_runner.planner import PlanGenerator
from llm_runner.plan_writer import PlanWriter


def read_agents_context(directory="."):
    """Read AGENTS.md if it exists for context
    
    Args:
        directory: Directory to search for AGENTS.md
        
    Returns:
        AGENTS.md content or empty string
    """
    agents_path = os.path.join(directory, "AGENTS.md")
    if os.path.exists(agents_path):
        try:
            with open(agents_path, "r") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def handle_plan_mode(request, output_dir=".", config=None, use_context=False):
    """Handle plan mode request
    
    Args:
        request: User's plan request
        output_dir: Directory to write plan.md to
        config: Configuration dict
        use_context: Whether to include AGENTS.md context
        
    Returns:
        Path to written plan file, or None if error
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
        
        # Get context if requested
        context = None
        if use_context:
            context = read_agents_context(output_dir)
        
        # Generate plan
        print(f"Generating plan for: {request}")
        generator = PlanGenerator(
            ollama_url=ollama_url,
            model=model,
            temperature=temperature
        )
        
        plan = generator.generate_plan(request, context=context)
        
        # Write plan to file
        writer = PlanWriter(output_dir=output_dir)
        filepath = writer.write_plan(plan, request=request)
        
        print(f"✓ Plan written to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"✗ Error generating plan: {e}")
        return None
