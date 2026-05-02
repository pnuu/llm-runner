"""Plan generation module using LLM"""
from llm_runner.llm import OllamaClient, check_ollama_connection


class Plan:
    """Represents a structured plan"""
    
    def __init__(self, title, approach, steps, notes=""):
        """Initialize a plan
        
        Args:
            title: Plan title
            approach: Overall approach/strategy
            steps: List of action steps
            notes: Additional notes
        """
        self.title = title
        self.approach = approach
        self.steps = steps if isinstance(steps, list) else [steps]
        self.notes = notes
    
    def to_markdown(self):
        """Convert plan to markdown format
        
        Returns:
            Markdown formatted plan
        """
        md = f"# {self.title}\n\n"
        md += "## Approach\n\n"
        md += f"{self.approach}\n\n"
        md += "## Steps\n\n"
        
        for i, step in enumerate(self.steps, 1):
            md += f"{i}. {step}\n"
        
        if self.notes:
            md += f"\n## Notes\n\n{self.notes}\n"
        
        return md


class PlanGenerator:
    """Generates plans using LLM"""
    
    def __init__(self, ollama_url="http://localhost:11434", model="mistral:7b", temperature=0.7):
        """Initialize plan generator
        
        Args:
            ollama_url: Ollama API endpoint
            model: Model to use
            temperature: Temperature for generation
            
        Raises:
            Exception: If Ollama not accessible
        """
        if not check_ollama_connection(ollama_url):
            raise Exception(f"Cannot connect to Ollama at {ollama_url}")
        
        self.client = OllamaClient(url=ollama_url)
        self.model = model
        self.temperature = temperature
    
    def generate_plan(self, request, context=None):
        """Generate a plan for the given request
        
        Args:
            request: User request/task description
            context: Optional additional context (e.g., AGENTS.md content)
            
        Returns:
            Plan object
        """
        # Build prompt
        prompt = self._build_prompt(request, context)
        
        # Get response from LLM
        response = self.client.send_prompt(
            prompt,
            model=self.model,
            temperature=self.temperature
        )
        
        # Parse response into Plan object
        plan = self._parse_response(response)
        return plan
    
    def _build_prompt(self, request, context=None):
        """Build the planning prompt
        
        Args:
            request: User request
            context: Optional context
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are a technical planning assistant. Create a detailed plan for the following request.

Request: {request}

"""
        
        if context:
            prompt += f"Context/Guidelines:\n{context}\n\n"
        
        prompt += """Please provide a plan in the following format:

Title: [Brief title of the plan]
Approach: [Overall strategy and approach]
Steps:
- [Step 1]
- [Step 2]
- [Step 3]
- ... (more steps as needed)
Notes: [Any important notes or considerations]

Be specific and actionable in your steps."""
        
        return prompt
    
    def _parse_response(self, response):
        """Parse LLM response into Plan object
        
        Args:
            response: LLM response text
            
        Returns:
            Plan object
        """
        lines = response.strip().split('\n')
        
        title = "Plan"
        approach = ""
        steps = []
        notes = ""
        
        section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Approach:"):
                section = "approach"
                approach = line.replace("Approach:", "").strip()
            elif line.startswith("Steps:"):
                section = "steps"
            elif line.startswith("Notes:"):
                section = "notes"
                notes = line.replace("Notes:", "").strip()
            elif line.startswith("-") and section == "steps":
                # Step item
                step = line.lstrip("-").strip()
                if step:
                    steps.append(step)
            elif section == "approach" and line and not line.startswith("-"):
                # Continuation of approach
                if approach:
                    approach += " " + line
                else:
                    approach = line
            elif section == "notes" and line:
                # Continuation of notes
                if notes:
                    notes += " " + line
                else:
                    notes = line
        
        # Ensure we have at least one step
        if not steps:
            steps = ["Execute the plan"]
        
        return Plan(
            title=title,
            approach=approach or "Execute the requested task",
            steps=steps,
            notes=notes
        )
