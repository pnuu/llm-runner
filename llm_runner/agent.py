"""Agent base class for autonomous task execution"""
import uuid
from typing import Optional, Dict, Any, List


class Agent:
    """Base class for autonomous agents that can execute tasks and spawn sub-agents"""
    
    def __init__(
        self,
        role: str,
        task: str,
        capabilities: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        llm_client=None,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize an Agent.
        
        Args:
            role: Agent's role (e.g., 'code', 'plan', 'research')
            task: The task this agent should execute
            capabilities: List of capabilities this agent has
            parent_id: ID of parent agent if spawned by another agent
            llm_client: OllamaClient instance for LLM communication
            workspace_dir: Isolated workspace directory for this agent
        """
        self.id = str(uuid.uuid4())[:8]
        self.role = role
        self.task = task
        self.capabilities = capabilities or []
        self.parent_id = parent_id
        self.llm_client = llm_client
        self.workspace_dir = workspace_dir
        
        self.status = "pending"
        self.result_store: Dict[str, Any] = {}
        self.sub_agents: Dict[str, "Agent"] = {}
    
    def store_result(self, key: str, value: Any) -> None:
        """Store a result in the result store"""
        self.result_store[key] = value
    
    def get_result(self, key: str) -> Any:
        """Retrieve a stored result"""
        return self.result_store.get(key)
    
    def execute(self, task: Optional[str] = None) -> str:
        """
        Execute the agent's task. Must be overridden by subclasses.
        
        Args:
            task: Optional task override
            
        Returns:
            Result string
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def spawn_agent(self, agent_type: str, task: str) -> "Agent":
        """
        Spawn a sub-agent to handle a sub-task.
        
        Args:
            agent_type: Type of agent to spawn ('code', 'plan', 'research', etc.)
            task: The task for the sub-agent
            
        Returns:
            The spawned sub-agent
        """
        sub_agent = Agent(
            role=agent_type,
            task=task,
            parent_id=self.id,
            llm_client=self.llm_client,
            workspace_dir=self.workspace_dir
        )
        self.sub_agents[sub_agent.id] = sub_agent
        return sub_agent
    
    def wait_for_agent(self, agent_id: str) -> str:
        """
        Wait for a sub-agent to complete and get its result.
        
        Args:
            agent_id: ID of the sub-agent
            
        Returns:
            Result from the sub-agent
        """
        if agent_id not in self.sub_agents:
            raise ValueError(f"Unknown sub-agent: {agent_id}")
        
        sub_agent = self.sub_agents[agent_id]
        
        if sub_agent.status == "pending":
            sub_agent.status = "running"
            result = sub_agent.execute()
            sub_agent.status = "complete"
        else:
            result = sub_agent.get_result("output")
        
        self.result_store[f"sub_agent_{agent_id}"] = sub_agent.result_store
        return result
