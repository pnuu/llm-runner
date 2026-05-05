"""Handler for plan mode"""
import os
from llm_runner.planner import PlanGenerator
from llm_runner.plan_writer import PlanWriter
from llm_runner.plan_outline import PlanOutlineExtractor
from llm_runner.plan_refinement import PlanRefinementDetector


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


def read_existing_plan(output_dir="."):
    """Read existing plan.md if it exists
    
    Args:
        output_dir: Directory to search for plan.md
        
    Returns:
        Plan content or None if not found
    """
    plan_path = os.path.join(output_dir, "plan.md")
    if os.path.exists(plan_path):
        try:
            with open(plan_path, "r") as f:
                return f.read()
        except Exception:
            return None
    return None


def display_plan_outline(plan_content):
    """Display condensed outline of plan
    
    Args:
        plan_content: Full plan.md content
    """
    if not plan_content:
        return
    
    extractor = PlanOutlineExtractor()
    outline = extractor.format_outline(plan_content, include_header=True)
    print(outline)


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


def handle_interactive_plan_refinement(output_dir="."):
    """Enter interactive plan refinement mode
    
    Display existing plan outline (if plan.md exists) and prepare to
    track refinements during interactive chat. This function sets up
    the plan context for use in interactive chat.
    
    Args:
        output_dir: Directory containing plan.md
        
    Returns:
        Dictionary with plan refinement state, or None if error
    """
    try:
        existing_plan = read_existing_plan(output_dir)
        
        if existing_plan:
            # Display outline of existing plan
            print()
            display_plan_outline(existing_plan)
            print()
            print("Plan added to conversation context. You can now refine it.")
            print()
            
            return {
                "has_existing_plan": True,
                "original_plan": existing_plan,
                "plan_path": os.path.join(output_dir, "plan.md")
            }
        else:
            print()
            print("No existing plan.md found. You can create a new plan.")
            print()
            
            return {
                "has_existing_plan": False,
                "original_plan": None,
                "plan_path": os.path.join(output_dir, "plan.md")
            }
    
    except Exception as e:
        print(f"✗ Error entering plan refinement mode: {e}")
        return None


def detect_and_save_plan_refinement(plan_state, chat_content, output_dir=".", config=None):
    """Detect plan refinements from chat and save to plan.md
    
    Args:
        plan_state: State dict from handle_interactive_plan_refinement()
        chat_content: Full chat conversation content
        output_dir: Directory containing plan.md
        config: Configuration dict
        
    Returns:
        True if plan was refined and saved, False otherwise
    """
    if not plan_state or not plan_state.get("original_plan"):
        return False
    
    try:
        # Detect if plan was refined
        detector = PlanRefinementDetector()
        
        if not detector.detect_changes(plan_state["original_plan"], chat_content):
            return False
        
        # Plan was refined - extract refined content and update
        refined_plan = detector.extract_refined_plan(chat_content, plan_state["original_plan"])
        
        if not refined_plan:
            return False
        
        # Save the refined plan
        writer = PlanWriter(output_dir=output_dir)
        
        # Create backup of original plan
        backup_path = writer._create_backup(plan_state["plan_path"])
        
        # Write refined plan
        with open(plan_state["plan_path"], "w") as f:
            f.write(refined_plan)
        
        print(f"✓ Plan refined and saved to: {plan_state['plan_path']}")
        if backup_path:
            print(f"  Backup saved to: {backup_path}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error saving plan refinement: {e}")
        return False
