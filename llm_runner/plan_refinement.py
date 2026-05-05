"""Plan refinement detection and extraction module"""
import re
from typing import Tuple, Optional


class PlanRefinementDetector:
    """Detect and extract plan refinements from chat content"""
    
    # Keywords that indicate plan changes
    CHANGE_KEYWORDS = {
        'add': 1.0,
        'new': 0.9,
        'create': 0.8,
        'implement': 0.7,
        'include': 0.7,
        'remove': 1.0,
        'delete': 1.0,
        'eliminate': 0.9,
        'drop': 0.7,
        'modify': 0.9,
        'change': 0.7,
        'update': 0.8,
        'revise': 0.8,
        'section': 0.8,
        'task': 0.8,
        'phase': 0.8,
        'step': 0.8,
        'strategy': 0.7,
        'approach': 0.6,
        'process': 0.6,
        'plan': 0.5,
        'updated': 0.8,
        'new': 0.9,
    }
    
    MIN_CONFIDENCE = 0.65  # Minimum confidence to detect change
    
    def __init__(self):
        """Initialize detector"""
        self.detected_changes = []
    
    def detect_changes(self, original_plan: str, chat_content: str) -> bool:
        """Detect if plan was meaningfully refined in chat
        
        Args:
            original_plan: Original plan.md content
            chat_content: Chat conversation content
            
        Returns:
            True if meaningful changes detected with high confidence
        """
        if not chat_content or not original_plan:
            return False
        
        self.detected_changes = []
        
        # Get confidence score
        score = self.get_confidence_score(original_plan, chat_content)
        
        # Return true if confidence exceeds threshold
        has_changes = score >= (self.MIN_CONFIDENCE - 0.05)  # Slightly lower threshold
        
        return has_changes
    
    def _analyze_for_keywords(self, text: str) -> float:
        """Analyze text for change keywords and return confidence
        
        Args:
            text: Text to analyze
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        found_keywords = {}
        
        # Look for change keywords
        for keyword, base_confidence in self.CHANGE_KEYWORDS.items():
            # Count keyword occurrences
            count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
            if count > 0:
                found_keywords[keyword] = base_confidence * min(count, 1.5)  # Cap at 1.5x
        
        # If we found change keywords, return average confidence
        if found_keywords:
            return sum(found_keywords.values()) / len(found_keywords)
        
        return 0.0
    
    def _detect_structural_changes(self, chat_content: str) -> float:
        """Detect structural changes like new sections or tasks
        
        Args:
            chat_content: Chat content to analyze
            
        Returns:
            Confidence score for structural changes
        """
        score = 0.0
        
        # Look for section markers (##, ###, etc.)
        section_markers = len(re.findall(r'^#+\s+', chat_content, re.MULTILINE))
        if section_markers > 0:
            score += 0.3
        
        # Look for bullet points (structured list)
        bullet_points = len(re.findall(r'^[\s]*[-*]\s+', chat_content, re.MULTILINE))
        if bullet_points > 2:  # More than 2 bullets suggests plan structure
            score += 0.3
        
        # Look for numbered items (step-by-step plan)
        numbered_items = len(re.findall(r'^\d+\.\s+', chat_content, re.MULTILINE))
        if numbered_items > 2:
            score += 0.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _extract_ai_responses(self, chat_content: str) -> list:
        """Extract AI response segments from chat
        
        Args:
            chat_content: Full chat content
            
        Returns:
            List of AI response strings
        """
        responses = []
        
        # Split by "User:" or "AI:" markers if they exist
        lines = chat_content.split('\n')
        current_response = []
        in_ai_response = False
        
        for i, line in enumerate(lines):
            # Check for markers
            if 'User:' in line or line.strip().startswith('>'):
                # End current AI response if any
                if in_ai_response and current_response:
                    responses.append('\n'.join(current_response).strip())
                current_response = []
                in_ai_response = False
            elif 'AI:' in line:
                # End previous response
                if in_ai_response and current_response:
                    responses.append('\n'.join(current_response).strip())
                current_response = []
                in_ai_response = True
                # Get content after "AI:"
                content = line.split('AI:', 1)[1].strip()
                if content:
                    current_response.append(content)
            elif in_ai_response:
                # Continue AI response
                if line.strip():  # Non-empty lines
                    current_response.append(line)
        
        # Don't forget last response
        if in_ai_response and current_response:
            responses.append('\n'.join(current_response).strip())
        
        return responses
    
    def _extract_user_requests(self, chat_content: str) -> list:
        """Extract user request segments from chat
        
        Args:
            chat_content: Full chat content
            
        Returns:
            List of user request strings
        """
        requests = []
        
        lines = chat_content.split('\n')
        
        for i, line in enumerate(lines):
            # Detect user input lines
            if 'User:' in line or line.strip().startswith('>'):
                # Extract everything after marker
                if 'User:' in line:
                    user_input = line.split('User:', 1)[1].strip()
                else:
                    user_input = line[1:].strip() if line.strip().startswith('>') else line.strip()
                
                if user_input:
                    requests.append(user_input)
                
                # Also check next lines for continuation (until next User: or AI: or empty line)
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j]
                    if 'User:' in next_line or 'AI:' in next_line or next_line.strip().startswith('>'):
                        break
                    if next_line.strip():
                        requests[-1] += f" {next_line.strip()}"
        
        return requests
    
    def extract_refined_plan(self, chat_content: str, original_plan: str) -> str:
        """Extract updated plan from chat responses
        
        Args:
            chat_content: Chat conversation content
            original_plan: Original plan.md content
            
        Returns:
            Extracted or refined plan text
        """
        if not chat_content:
            return original_plan
        
        # Look for markdown sections that look like plans
        plan_sections = self._extract_plan_sections(chat_content)
        
        if plan_sections:
            # Return extracted plan sections
            return '\n\n'.join(plan_sections)
        
        # If no clear plan extraction, return original
        return original_plan
    
    def _extract_plan_sections(self, chat_content: str) -> list:
        """Extract plan-like sections from chat
        
        Args:
            chat_content: Chat content
            
        Returns:
            List of plan section strings
        """
        sections = []
        
        # Look for markdown headers followed by content
        lines = chat_content.split('\n')
        
        current_section = []
        in_section = False
        
        for line in lines:
            # Detect headers (##, ###, etc.)
            if re.match(r'^#+\s+', line):
                # If we have accumulated a section, save it
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:
                        sections.append(section_text)
                
                current_section = [line]
                in_section = True
            elif in_section:
                # Continue accumulating section content
                if line.strip():  # Non-empty lines
                    current_section.append(line)
                elif current_section and len(current_section) > 1:
                    # Empty line after accumulating content - might end section
                    pass
        
        # Don't forget last section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                sections.append(section_text)
        
        return sections
    
    def get_confidence_score(self, original_plan: str, chat_content: str) -> float:
        """Get confidence score for detected changes (0.0 to 1.0)
        
        Args:
            original_plan: Original plan.md
            chat_content: Chat content
            
        Returns:
            Confidence score
        """
        if not chat_content or not original_plan:
            return 0.0
        
        ai_responses = self._extract_ai_responses(chat_content)
        user_requests = self._extract_user_requests(chat_content)
        
        # Analyze keyword mentions
        keyword_score = 0.0
        
        for response in ai_responses:
            keyword_score += self._analyze_for_keywords(response)
        
        for request in user_requests:
            keyword_score += self._analyze_for_keywords(request)
        
        total_messages = len(ai_responses) + len(user_requests)
        if total_messages > 0:
            keyword_score = keyword_score / total_messages
        
        # Analyze structural changes
        structural_score = self._detect_structural_changes(chat_content)
        
        # Combine scores: give more weight to structural changes (0.4) and keywords (0.6)
        combined_score = (keyword_score * 0.6) + (structural_score * 0.4)
        
        return min(combined_score, 1.0)  # Normalize to 0.0-1.0
