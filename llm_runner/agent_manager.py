"""Agent lifecycle management"""
from typing import Dict, Optional, List
from llm_runner.agent import Agent


class AgentManager:
    """Manages agent lifecycle, registry, and parent-child relationships"""
    
    def __init__(self):
        """Initialize the agent manager"""
        self.agents: Dict[str, Agent] = {}
        self.parent_child_graph: Dict[str, str] = {}  # child_id -> parent_id
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent in the manager.
        
        Args:
            agent: Agent instance to register
        """
        self.agents[agent.id] = agent
        if agent.parent_id:
            self.parent_child_graph[agent.id] = agent.parent_id
    
    def spawn_agent(
        self,
        role: str,
        task: str,
        parent_id: Optional[str] = None,
        parent_of: Optional[str] = None
    ) -> Agent:
        """
        Spawn a new agent and register it.
        
        Args:
            role: Agent's role
            task: Task for the agent
            parent_id: ID of parent agent if this is a sub-agent
            parent_of: ID of agent this would be parent of (for cycle detection)
            
        Returns:
            The spawned agent
            
        Raises:
            ValueError: If circular delegation would occur
        """
        # Check for circular delegation
        if parent_id and parent_of:
            if self._would_create_cycle(parent_id, parent_of):
                raise ValueError("Cannot create circular delegation")
        
        agent = Agent(
            role=role,
            task=task,
            parent_id=parent_id,
            llm_client=None
        )
        
        self.register_agent(agent)
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            The agent or None if not found
        """
        return self.agents.get(agent_id)
    
    def cleanup_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: ID of the agent to clean up
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
        if agent_id in self.parent_child_graph:
            del self.parent_child_graph[agent_id]
    
    def list_active_agents(self) -> List[Agent]:
        """
        Get list of all active agents.
        
        Returns:
            List of active agents
        """
        return list(self.agents.values())
    
    def count_agents(self) -> int:
        """
        Count active agents.
        
        Returns:
            Number of active agents
        """
        return len(self.agents)
    
    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """
        Check if making parent_id the parent of child_id would create a cycle.
        
        Args:
            parent_id: Proposed parent
            child_id: Proposed child
            
        Returns:
            True if cycle would occur
        """
        # Walk up the chain from parent_id
        visited = set()
        current = parent_id
        
        while current:
            if current == child_id:
                return True
            if current in visited:
                break  # Cycle detected in existing graph
            visited.add(current)
            current = self.parent_child_graph.get(current)
        
        return False
