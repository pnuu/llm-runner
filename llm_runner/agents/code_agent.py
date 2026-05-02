"""CodeAgent for file creation and coding tasks"""
from llm_runner.agent import Agent


class CodeAgent(Agent):
    """Specialized agent for code generation and file creation"""
    
    def __init__(self, task: str, llm_client=None, workspace_dir=None, parent_id=None):
        """Initialize CodeAgent"""
        super().__init__(
            role="code",
            task=task,
            capabilities=["coding", "file_creation", "debugging", "testing"],
            parent_id=parent_id,
            llm_client=llm_client,
            workspace_dir=workspace_dir
        )
    
    def execute(self, task=None):
        """Execute code generation task"""
        task = task or self.task
        self.status = "running"
        
        # Use LLM to generate code
        if self.llm_client:
            result = self.llm_client.send_prompt(
                f"Generate code for: {task}"
            )
        else:
            result = f"Code generation placeholder for: {task}"
        
        self.store_result("output", result)
        self.status = "complete"
        return result
