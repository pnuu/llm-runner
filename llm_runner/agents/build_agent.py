"""BuildAgent for execution and command running"""
from llm_runner.agent import Agent


class BuildAgent(Agent):
    """Specialized agent for build and execution tasks"""
    
    def __init__(self, task: str, llm_client=None, workspace_dir=None, parent_id=None):
        """Initialize BuildAgent"""
        super().__init__(
            role="build",
            task=task,
            capabilities=["execution", "command_execution", "file_management", "testing"],
            parent_id=parent_id,
            llm_client=llm_client,
            workspace_dir=workspace_dir
        )
    
    def execute(self, task=None):
        """Execute build task"""
        task = task or self.task
        self.status = "running"
        
        # Use LLM to plan build
        if self.llm_client:
            result = self.llm_client.send_prompt(
                f"Execute build: {task}"
            )
        else:
            result = f"Build execution placeholder for: {task}"
        
        self.store_result("output", result)
        self.status = "complete"
        return result
