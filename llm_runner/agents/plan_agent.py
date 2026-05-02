"""PlanAgent for task decomposition and planning"""
import re
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
    
    def decompose_task(self):
        """Decompose task into sub-tasks using LLM"""
        self.status = "running"
        
        prompt = f"""Decompose this task into sub-tasks with agent types:
Task: {self.task}

Format each sub-task as:
- AgentType: description

Agent types available: CodeAgent, TestAgent, ResearchAgent, BuildAgent, PlanAgent"""
        
        if self.llm_client:
            response = self.llm_client.send_prompt(prompt)
        else:
            response = f"Sub-tasks for: {self.task}"
        
        sub_tasks = self._parse_decomposition(response)
        self.store_result("decomposition", sub_tasks)
        
        return response
    
    def _parse_decomposition(self, response: str):
        """Parse LLM decomposition response into structured sub-tasks"""
        sub_tasks = []
        
        # Match lines like "1. CodeAgent: Create file" or "- CodeAgent: Create file"
        pattern = r'[-\d.]+\s*(\w+Agent):\s*(.+?)(?=\n|$)'
        matches = re.findall(pattern, response)
        
        for agent_type, description in matches:
            sub_tasks.append({
                "agent_type": agent_type,
                "task": description.strip()
            })
        
        return sub_tasks
