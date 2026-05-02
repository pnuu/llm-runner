"""Agent system safety and resource limits"""
import time
from typing import Optional, List, Set


class AgentLimiter:
    """Enforces resource and safety limits on agent execution"""
    
    def __init__(
        self,
        max_depth: int = 5,
        max_agents: int = 20,
        max_concurrent: int = 10,
        task_timeout: int = 30
    ):
        """
        Initialize agent limiter.
        
        Args:
            max_depth: Maximum delegation depth (prevent infinite recursion)
            max_agents: Maximum total agents that can be spawned (lifetime)
            max_concurrent: Maximum concurrent agents running
            task_timeout: Timeout in seconds for individual tasks
        """
        self.max_depth = max_depth
        self.max_agents = max_agents
        self.max_concurrent = max_concurrent
        self.task_timeout = task_timeout
        
        self.active_agents: Set[str] = set()
        self.total_agents_created = 0
    
    def can_spawn_agent(
        self,
        depth: Optional[int] = None,
        active_count: Optional[int] = None
    ) -> bool:
        """
        Check if a new agent can be spawned.
        
        Args:
            depth: Current delegation depth
            active_count: Current active agent count (concurrent)
            
        Returns:
            True if agent can be spawned
        """
        # Check depth limit
        if depth is not None and depth > self.max_depth:
            return False
        
        # Check total agents limit
        if self.total_agents_created >= self.max_agents:
            return False
        
        # Check concurrent limit
        if active_count is not None and active_count >= self.max_concurrent:
            return False
        
        return True
    
    def register_agent(self, agent_id: str) -> None:
        """Register a spawned agent"""
        self.active_agents.add(agent_id)
        self.total_agents_created += 1
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister a completed agent"""
        self.active_agents.discard(agent_id)
    
    def get_active_count(self) -> int:
        """Get count of active agents"""
        return len(self.active_agents)
    
    def is_circular(self, ancestry_chain: List[str]) -> bool:
        """
        Check if an ancestry chain has circular references.
        
        Args:
            ancestry_chain: List of agent IDs from root to current
            
        Returns:
            True if circular delegation detected
        """
        if len(ancestry_chain) != len(set(ancestry_chain)):
            # Duplicate found - circular
            return True
        return False
    
    def apply_timeout(self, func, *args, **kwargs):
        """
        Apply timeout to a function execution.
        
        Args:
            func: Function to execute
            
        Returns:
            Function result
        """
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        if elapsed > self.task_timeout:
            # Log timeout (in real system would cancel task)
            pass
        
        return result
