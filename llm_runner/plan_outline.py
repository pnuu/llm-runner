"""Plan outline extraction and formatting module"""
import re


class PlanOutlineExtractor:
    """Extract condensed outlines from plan.md files"""
    
    MAX_LINES = 30
    MAX_SECTION_BULLETS = 3
    
    def __init__(self):
        """Initialize extractor"""
        self.lines = []
    
    def extract_summary(self, plan_content: str) -> str:
        """Extract condensed outline from plan.md
        
        Args:
            plan_content: Full plan.md file content
            
        Returns:
            Condensed outline (max 30 lines) showing key sections and objectives
        """
        if not plan_content or not plan_content.strip():
            return ""
        
        self.lines = []
        lines = plan_content.split('\n')
        
        in_code_block = False
        current_section_level = 0
        section_bullets = {}  # Track bullets per section
        
        for i, line in enumerate(lines):
            # Track code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                continue
            
            # Extract headers as sections
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                
                # Skip unimportant headers
                if text.lower() in ['overview', 'notes', 'implementation']:
                    current_section_level = level
                    continue
                
                # Add section header with indentation
                indent = "  " * (level - 1)
                self._add_line(f"{indent}• {text}")
                current_section_level = level
                section_bullets[level] = 0
                continue
            
            # Extract bullet points under sections
            if line.strip().startswith(('-', '*')):
                # Only take first few bullets per section
                if current_section_level > 0:
                    if section_bullets.get(current_section_level, 0) < self.MAX_SECTION_BULLETS:
                        bullet_text = re.sub(r'^[\s\-\*]+', '', line).strip()
                        if bullet_text:
                            indent = "    " * (current_section_level - 1)
                            self._add_line(f"{indent}- {bullet_text}")
                            section_bullets[current_section_level] = section_bullets.get(current_section_level, 0) + 1
        
        # Add status/notes at end if found
        status_info = self._extract_status_info(plan_content)
        if status_info:
            self._add_line("")
            self._add_line(f"Status: {status_info}")
        
        # Limit to MAX_LINES
        result = '\n'.join(self.lines[:self.MAX_LINES])
        return result.strip()
    
    def _add_line(self, line: str) -> None:
        """Add line to output, checking length limit"""
        if len(self.lines) < self.MAX_LINES:
            self.lines.append(line)
    
    def _extract_status_info(self, content: str) -> str:
        """Extract status or completion info from plan"""
        # Look for Status: or Completed: lines
        for line in content.split('\n'):
            if re.match(r'^Status:', line, re.IGNORECASE):
                return re.sub(r'^Status:\s*', '', line, flags=re.IGNORECASE).strip()
            if re.match(r'^Completed?:', line, re.IGNORECASE):
                match = re.search(r'Completed?:\s*(.+)', line, re.IGNORECASE)
                if match:
                    return f"Completion: {match.group(1)}"
        return ""
    
    def format_outline(self, plan_content: str, include_header: bool = True) -> str:
        """Format plan outline for display
        
        Args:
            plan_content: Full plan.md content
            include_header: Whether to add header line
            
        Returns:
            Formatted outline ready for display
        """
        outline = self.extract_summary(plan_content)
        
        if not outline:
            return "(No plan content to display)"
        
        if include_header:
            return f"\n=== Current Plan Summary ===\n\n{outline}\n"
        
        return outline
