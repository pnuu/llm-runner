"""LLM Tool calling system - manages available tools and executes them"""
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import xml.etree.ElementTree as ET


class ToolResult:
    """Result of tool execution"""
    
    def __init__(self, success: bool, message: str, data: Any = None):
        """Initialize tool result
        
        Args:
            success: Whether tool executed successfully
            message: Result message for LLM and user
            data: Optional result data
        """
        self.success = success
        self.message = message
        self.data = data
    
    def __str__(self):
        """String representation for feeding back to LLM"""
        status = "SUCCESS" if self.success else "ERROR"
        return f"[TOOL RESULT: {status}] {self.message}"


class FileWriteTool:
    """Tool for writing text to files"""
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        """Initialize file write tool
        
        Args:
            allowed_dirs: List of allowed directories (default: current dir and home)
        """
        if allowed_dirs is None:
            allowed_dirs = [
                ".",
                str(Path.home()),
                str(Path.home() / "Documents"),
            ]
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs]
    
    def _is_safe_path(self, filepath: str) -> Tuple[bool, str]:
        """Check if path is safe to write to
        
        Args:
            filepath: Path to check
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        abs_path = os.path.abspath(filepath)
        
        # Check if path is within allowed directories
        for allowed_dir in self.allowed_dirs:
            if abs_path.startswith(allowed_dir):
                return True, ""
        
        return False, f"Path '{filepath}' is outside allowed directories: {self.allowed_dirs}"
    
    def execute(self, path: str, content: str, append: bool = False) -> ToolResult:
        """Write content to file
        
        Args:
            path: File path to write to
            content: Content to write
            append: If True, append to file instead of overwriting
            
        Returns:
            ToolResult with status and message
        """
        # Safety check
        is_safe, error_msg = self._is_safe_path(path)
        if not is_safe:
            return ToolResult(False, error_msg)
        
        try:
            # Create parent directories if needed
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
            
            # Write or append
            mode = "a" if append else "w"
            with open(path, mode) as f:
                f.write(content)
            
            abs_path = os.path.abspath(path)
            action = "Appended to" if append else "Created"
            return ToolResult(
                True,
                f"{action} file: {abs_path} ({len(content)} bytes)",
                {"path": abs_path, "bytes_written": len(content)}
            )
        
        except Exception as e:
            return ToolResult(False, f"Failed to write file: {str(e)}")


class ToolsManager:
    """Manages available tools and executes tool calls from LLM responses"""
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        """Initialize tools manager
        
        Args:
            allowed_dirs: Allowed directories for file operations
        """
        self.tools = {
            "write_file": FileWriteTool(allowed_dirs=allowed_dirs)
        }
        
        # Tool schemas for system prompt
        self.tool_schemas = {
            "write_file": {
                "description": "Write text content to a file",
                "format": '<tool name="write_file"><path>filename.txt</path><content>Your content here</content><append>false</append></tool>',
                "parameters": {
                    "path": "File path to write to (required)",
                    "content": "Content to write (required)",
                    "append": "If true, append instead of overwriting (optional, default: false)"
                }
            }
        }
    
    def get_tools_description(self) -> str:
        """Get description of available tools for system prompt
        
        Returns:
            Formatted string describing available tools
        """
        description = "AVAILABLE TOOLS:\n\n"
        
        for tool_name, schema in self.tool_schemas.items():
            description += f"Tool: {tool_name}\n"
            description += f"Description: {schema['description']}\n"
            description += f"Format: {schema['format']}\n"
            description += "Parameters:\n"
            for param, param_desc in schema['parameters'].items():
                description += f"  - {param}: {param_desc}\n"
            description += "\n"
        
        return description
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from model response
        
        Looks for <tool>...</tool> tags in the response
        
        Args:
            response: Model response text
            
        Returns:
            List of tool call dictionaries
        """
        tool_calls = []
        
        # Find all <tool>...</tool> tags
        pattern = r'<tool\s+name="(\w+)">(.*?)</tool>'
        matches = re.finditer(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            tool_name = match.group(1).lower()
            tool_content = match.group(2)
            
            # Parse tool parameters from XML
            try:
                params = self._parse_tool_params(tool_content)
                tool_calls.append({
                    "name": tool_name,
                    "params": params,
                    "raw": match.group(0)
                })
            except Exception as e:
                # Silently skip malformed tool calls
                continue
        
        return tool_calls
    
    def _parse_tool_params(self, xml_content: str) -> Dict[str, str]:
        """Parse parameters from XML-formatted tool content
        
        Args:
            xml_content: XML content between <tool>...</tool> tags
            
        Returns:
            Dictionary of parameters
        """
        params = {}
        
        # Try to parse as XML
        try:
            # Wrap in root element for parsing
            xml_str = f"<root>{xml_content}</root>"
            root = ET.fromstring(xml_str)
            
            for child in root:
                params[child.tag.lower()] = child.text or ""
        
        except ET.ParseError:
            # Fallback: try to extract key-value pairs
            lines = xml_content.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Try pattern like <key>value</key>
                match = re.match(r'<(\w+)>(.*?)</\1>', line)
                if match:
                    params[match.group(1).lower()] = match.group(2)
        
        return params
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given parameters
        
        Args:
            tool_name: Name of tool to execute
            params: Parameters to pass to tool
            
        Returns:
            ToolResult with execution result
        """
        tool_name = tool_name.lower()
        
        if tool_name not in self.tools:
            return ToolResult(False, f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        
        try:
            if tool_name == "write_file":
                # Handle boolean append parameter
                append = params.get("append", "false").lower() in ("true", "1", "yes")
                return tool.execute(
                    path=params.get("path", ""),
                    content=params.get("content", ""),
                    append=append
                )
            else:
                return ToolResult(False, f"Tool {tool_name} execution not implemented")
        
        except TypeError as e:
            return ToolResult(False, f"Invalid parameters for {tool_name}: {str(e)}")
        except Exception as e:
            return ToolResult(False, f"Error executing {tool_name}: {str(e)}")
    
    def execute_tool_calls(self, response: str) -> Tuple[List[ToolResult], str]:
        """Execute all tool calls found in response
        
        Args:
            response: Model response containing tool calls
            
        Returns:
            Tuple of (list of tool results, response with tool calls removed)
        """
        tool_calls = self.parse_tool_calls(response)
        results = []
        modified_response = response
        
        for tool_call in tool_calls:
            result = self.execute_tool(tool_call["name"], tool_call["params"])
            results.append(result)
            
            # Remove tool call from response
            modified_response = modified_response.replace(tool_call["raw"], "")
        
        return results, modified_response.strip()
    
    def get_system_prompt_extension(self) -> str:
        """Get system prompt text to enable tool calling
        
        Returns:
            String to append to system prompt
        """
        return f"""
You have access to the following tools to help users:

{self.get_tools_description()}

When you need to use a tool, include it in your response using the format shown above.
You can use multiple tools in a single response.
After using a tool, the result will be shown to you, and you can then continue your response.
"""


# Convenience function
def create_tools_manager(allowed_dirs: Optional[List[str]] = None) -> ToolsManager:
    """Create and return a tools manager instance
    
    Args:
        allowed_dirs: Allowed directories for file operations
        
    Returns:
        Initialized ToolsManager
    """
    return ToolsManager(allowed_dirs=allowed_dirs)
