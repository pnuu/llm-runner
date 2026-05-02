"""Build executor with tool system"""
import os
import subprocess


def create_file_tool(filepath, content):
    """Create a new file
    
    Args:
        filepath: Path to file to create
        content: File content
        
    Returns:
        Success/error message
    """
    # Check if file exists
    if os.path.exists(filepath):
        return f"Error: File already exists: {filepath}"
    
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            f.write(content)
        
        return f"Created file: {filepath} ({len(content)} bytes)"
    except Exception as e:
        return f"Error creating file: {str(e)}"


def write_file_tool(filepath, content):
    """Write/append to a file
    
    Args:
        filepath: Path to file
        content: Content to write
        
    Returns:
        Success/error message
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            f.write(content)
        
        return f"Wrote to file: {filepath} ({len(content)} bytes)"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def read_file_tool(filepath):
    """Read file content
    
    Args:
        filepath: Path to file
        
    Returns:
        File content or error message
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: File not found: {filepath}"
        
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def run_command_tool(command):
    """Run a shell command
    
    Args:
        command: Shell command to run
        
    Returns:
        Command output or error message
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += result.stderr
        
        if result.returncode != 0:
            return f"Error (exit code {result.returncode}): {output}"
        
        return output if output else "Command executed successfully"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s)"
    except Exception as e:
        return f"Error running command: {str(e)}"


class BuildExecutor:
    """Executor for build mode operations"""
    
    def __init__(self, workspace_dir="."):
        """Initialize executor
        
        Args:
            workspace_dir: Directory for file operations
        """
        self.workspace_dir = workspace_dir
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Define available tools
        self.tools = {
            "create_file": self._tool_create_file,
            "write_file": self._tool_write_file,
            "read_file": self._tool_read_file,
            "run_command": self._tool_run_command,
        }
        
        # Track created files
        self.created_files = []
        self.executed_commands = []
    
    def _resolve_path(self, filepath):
        """Resolve filepath relative to workspace
        
        Args:
            filepath: File path (relative or absolute)
            
        Returns:
            Resolved absolute path
        """
        if os.path.isabs(filepath):
            return filepath
        return os.path.join(self.workspace_dir, filepath)
    
    def _tool_create_file(self, filepath, content):
        """Tool: create file
        
        Args:
            filepath: Path to create
            content: File content
            
        Returns:
            Result message
        """
        full_path = self._resolve_path(filepath)
        result = create_file_tool(full_path, content)
        
        if "created" in result.lower():
            self.created_files.append(full_path)
        
        return result
    
    def _tool_write_file(self, filepath, content):
        """Tool: write to file
        
        Args:
            filepath: Path to write
            content: Content
            
        Returns:
            Result message
        """
        full_path = self._resolve_path(filepath)
        return write_file_tool(full_path, content)
    
    def _tool_read_file(self, filepath):
        """Tool: read file
        
        Args:
            filepath: Path to read
            
        Returns:
            File content or error
        """
        full_path = self._resolve_path(filepath)
        return read_file_tool(full_path)
    
    def _tool_run_command(self, command):
        """Tool: run command
        
        Args:
            command: Command to run
            
        Returns:
            Command output or error
        """
        result = run_command_tool(command)
        self.executed_commands.append(command)
        return result
    
    def execute_tool(self, tool_name, args):
        """Execute a tool
        
        Args:
            tool_name: Name of tool
            args: List of arguments for tool
            
        Returns:
            Tool output/result
        """
        if tool_name not in self.tools:
            return f"Error: Unknown tool: {tool_name}"
        
        try:
            tool = self.tools[tool_name]
            return tool(*args)
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    def get_summary(self):
        """Get summary of executor actions
        
        Returns:
            Summary string
        """
        summary = "Build Summary:\n"
        summary += f"Files created: {len(self.created_files)}\n"
        summary += f"Commands executed: {len(self.executed_commands)}\n"
        
        if self.created_files:
            summary += "\nCreated files:\n"
            for f in self.created_files:
                summary += f"  - {f}\n"
        
        if self.executed_commands:
            summary += "\nExecuted commands:\n"
            for cmd in self.executed_commands:
                summary += f"  - {cmd}\n"
        
        return summary
