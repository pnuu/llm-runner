"""PlanAgent for task decomposition and planning"""
from llm_runner.agent import Agent


class PlanAgent(Agent):
    """Specialized agent for task planning and decomposition"""
    
    def __init__(self, task: str, llm_client=None, workspace_dir=None, parent_id=None):
        """Initialize PlanAgent"""
        super().__init__(
            role="plan",
            task=task,
            capabilities=["planning", "decomposition", "analysis", "sequencing"],
            parent_id=parent_id,
            llm_client=llm_client,
            workspace_dir=workspace_dir
        )
    
    def execute(self, task=None):
        """Execute task planning"""
        task = task or self.task
        self.status = "running"
        
        # Use LLM to plan
        if self.llm_client:
            result = self.llm_client.send_prompt(
                f"Create a plan for: {task}"
            )
        else:
            result = f"Plan placeholder for: {task}"
        
        self.store_result("output", result)
        self.status = "complete"
        return result
