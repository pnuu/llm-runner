"""TestAgent for testing and validation tasks"""
from llm_runner.agent import Agent


class TestAgent(Agent):
    """Specialized agent for testing and validation"""
    
    def __init__(self, task: str, llm_client=None, workspace_dir=None, parent_id=None):
        """Initialize TestAgent"""
        super().__init__(
            role="test",
            task=task,
            capabilities=["testing", "validation", "quality_assurance", "debugging"],
            parent_id=parent_id,
            llm_client=llm_client,
            workspace_dir=workspace_dir
        )
    
    def execute(self, task=None):
        """Execute testing task"""
        task = task or self.task
        self.status = "running"
        
        # Use LLM to test
        if self.llm_client:
            result = self.llm_client.send_prompt(
                f"Test: {task}"
            )
        else:
            result = f"Test execution placeholder for: {task}"
        
        self.store_result("output", result)
        self.status = "complete"
        return result
