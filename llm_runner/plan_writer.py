"""Plan file writer module"""
import os
from datetime import datetime


class PlanWriter:
    """Writes plan objects to markdown files"""
    
    def __init__(self, output_dir="."):
        """Initialize plan writer
        
        Args:
            output_dir: Directory to write plans to
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def write_plan(self, plan, request="", filepath=None):
        """Write a plan to markdown file
        
        Args:
            plan: Plan object to write
            request: Original user request (optional)
            filepath: Specific filepath to write to (default: plan.md in output_dir)
            
        Returns:
            Path to written file
        """
        if filepath is None:
            filepath = os.path.join(self.output_dir, "plan.md")
        
        # Build content with metadata
        content = self._build_content(plan, request)
        
        # Write to file
        with open(filepath, "w") as f:
            f.write(content)
        
        return filepath
    
    def _build_content(self, plan, request):
        """Build the file content with metadata
        
        Args:
            plan: Plan object
            request: Original request
            
        Returns:
            Formatted file content
        """
        content = f"""# {plan.title}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if request:
            content += f"**Request:** {request}\n\n"
        
        content += plan.to_markdown()
        
        return content
