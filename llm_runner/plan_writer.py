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
    
    def _create_backup(self, filepath):
        """Create backup of existing file before modification
        
        Args:
            filepath: Path to file to backup
            
        Returns:
            Path to backup file, or None if original doesn't exist
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            # Create backups directory if needed
            backup_dir = os.path.join(os.path.dirname(filepath) or ".", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            base_name = os.path.basename(filepath)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{base_name}.{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Copy file to backup
            with open(filepath, "r") as f:
                content = f.read()
            
            with open(backup_path, "w") as f:
                f.write(content)
            
            return backup_path
        except Exception:
            return None
    
    def write_refined_plan(self, refined_content, filepath=None):
        """Write refined plan content to file with backup
        
        Used when saving refinements detected from chat conversation.
        Creates backup of original before overwriting.
        
        Args:
            refined_content: Full refined plan markdown content
            filepath: Path to plan file (default: plan.md in output_dir)
            
        Returns:
            Tuple of (success: bool, backup_path: str or None, filepath: str)
        """
        if filepath is None:
            filepath = os.path.join(self.output_dir, "plan.md")
        
        try:
            # Create backup if file exists
            backup_path = self._create_backup(filepath)
            
            # Write refined content
            with open(filepath, "w") as f:
                f.write(refined_content)
            
            return (True, backup_path, filepath)
        
        except Exception as e:
            return (False, None, str(e))
