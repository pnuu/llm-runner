"""ResearchAgent for information gathering and analysis"""
from llm_runner.agent import Agent


class ResearchAgent(Agent):
    """Specialized agent for research and analysis tasks"""
    
    def __init__(self, task: str, llm_client=None, workspace_dir=None, parent_id=None):
        """Initialize ResearchAgent"""
        super().__init__(
            role="research",
            task=task,
            capabilities=["research", "analysis", "summarization", "verification"],
            parent_id=parent_id,
            llm_client=llm_client,
            workspace_dir=workspace_dir
        )
    
    def execute(self, task=None):
        """Execute research task"""
        task = task or self.task
        self.status = "running"
        
        # Use LLM to research
        if self.llm_client:
            result = self.llm_client.send_prompt(
                f"Research and analyze: {task}"
            )
        else:
            result = f"Research placeholder for: {task}"
        
        self.store_result("output", result)
        self.status = "complete"
        return result
