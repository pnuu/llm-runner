"""Agent orchestration for multi-agent coordination"""
from typing import List, Dict, Any, Optional
import time
from llm_runner.agent_manager import AgentManager
from llm_runner.agents.code_agent import CodeAgent
from llm_runner.agents.plan_agent import PlanAgent
from llm_runner.agents.research_agent import ResearchAgent
from llm_runner.agents.build_agent import BuildAgent
from llm_runner.agents.test_agent import TestAgent


class AgentOrchestrator:
    """Orchestrates multi-agent execution (sequential, parallel, with error handling)"""
    
    AGENT_TYPES = {
        "CodeAgent": CodeAgent,
        "PlanAgent": PlanAgent,
        "ResearchAgent": ResearchAgent,
        "BuildAgent": BuildAgent,
        "TestAgent": TestAgent,
    }
    
    def __init__(self, manager: Optional[AgentManager] = None):
        """Initialize orchestrator"""
        self.manager = manager or AgentManager()
        self.execution_history: List[Dict[str, Any]] = []
        self.agent_results: Dict[str, Any] = {}
    
    def execute_sequential(
        self,
        tasks: List[Dict[str, str]],
        on_error: str = "abort"
    ) -> Dict[str, Any]:
        """
        Execute tasks sequentially, one after another.
        
        Args:
            tasks: List of tasks with agent_type and task
            on_error: What to do on failure: "abort", "skip", "retry"
            
        Returns:
            Execution result
        """
        for i, task in enumerate(tasks):
            agent_type = task.get("agent_type")
            task_desc = task.get("task")
            
            try:
                agent = self._create_agent(agent_type, task_desc)
                result = agent.execute()
                
                self.execution_history.append({
                    "index": i,
                    "agent_id": agent.id,
                    "agent_type": agent_type,
                    "status": "complete",
                    "result": result
                })
                
                self.agent_results[agent.id] = agent.result_store
                
            except Exception as e:
                if on_error == "abort":
                    return {"status": "failed", "error": str(e), "tasks_completed": i}
                elif on_error == "skip":
                    self.execution_history.append({
                        "index": i,
                        "agent_type": agent_type,
                        "status": "skipped",
                        "error": str(e)
                    })
        
        return {"status": "complete", "tasks_completed": len(tasks)}
    
    def execute_parallel(
        self,
        tasks: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Execute tasks in parallel (mocked - in real system uses threading/multiprocessing).
        
        Args:
            tasks: List of tasks
            
        Returns:
            Execution result
        """
        # Simplified parallel execution (in reality would use threading/multiprocessing)
        for task in tasks:
            agent_type = task.get("agent_type")
            task_desc = task.get("task")
            
            agent = self._create_agent(agent_type, task_desc)
            result = agent.execute()
            
            self.agent_results[agent.id] = agent.result_store
            self.execution_history.append({
                "agent_id": agent.id,
                "agent_type": agent_type,
                "status": "complete"
            })
        
        return {"status": "complete", "tasks_completed": len(tasks)}
    
    def execute_with_retry(
        self,
        task: Dict[str, str],
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Execute a task with retry on failure.
        
        Args:
            task: Task to execute
            max_retries: Maximum number of retries
            
        Returns:
            Result or None
        """
        for attempt in range(max_retries):
            try:
                agent_type = task.get("agent_type")
                task_desc = task.get("task")
                
                agent = self._create_agent(agent_type, task_desc)
                result = agent.execute()
                
                self.agent_results[agent.id] = agent.result_store
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    return None
    
    def aggregate_results(self) -> Dict[str, Any]:
        """
        Aggregate results from all executed agents.
        
        Returns:
            Dictionary of aggregated results
        """
        return self.agent_results.copy()
    
    def generate_execution_tree(self) -> Dict[str, Any]:
        """
        Generate a tree showing which agents executed and their relationships.
        
        Returns:
            Execution tree structure
        """
        tree = {}
        
        for entry in self.execution_history:
            agent_id = entry.get("agent_id")
            if agent_id:
                tree[agent_id] = {
                    "type": entry.get("agent_type"),
                    "status": entry.get("status"),
                    "result": entry.get("result")
                }
        
        return tree
    
    def _create_agent(self, agent_type: str, task: str, parent_id: Optional[str] = None):
        """
        Create an agent of specified type.
        
        Args:
            agent_type: Type of agent to create
            task: Task for the agent
            parent_id: Parent agent ID if sub-agent
            
        Returns:
            Agent instance
        """
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self.AGENT_TYPES[agent_type]
        return agent_class(task=task, parent_id=parent_id)
    
    def _create_agent_with_context(
        self,
        agent_type: str,
        task: str,
        context: Dict[str, Any]
    ):
        """
        Create an agent with context information.
        
        Args:
            agent_type: Type of agent
            task: Task for the agent
            context: Context dict with config, workspace, etc.
            
        Returns:
            Agent instance with context
        """
        agent = self._create_agent(agent_type, task)
        agent.context = context
        return agent
