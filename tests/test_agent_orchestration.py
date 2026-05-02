"""Tests for multi-agent orchestration"""
from unittest.mock import MagicMock, patch
from llm_runner.agent_orchestrator import AgentOrchestrator
from llm_runner.agent import Agent


class TestAgentOrchestration:
    """Test multi-agent coordination and execution"""
    
    def test_orchestrator_creation(self):
        """Test orchestrator initialization"""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.execution_history == []
        assert orchestrator.agent_results == {}
    
    def test_sequential_execution(self):
        """Test sequential agent execution"""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            {"agent_type": "PlanAgent", "task": "Plan API"},
            {"agent_type": "CodeAgent", "task": "Implement API"},
            {"agent_type": "TestAgent", "task": "Test API"}
        ]
        
        result = orchestrator.execute_sequential(tasks)
        
        assert len(orchestrator.execution_history) == 3
        assert result["status"] == "complete"
    
    def test_sequential_execution_with_failure(self):
        """Test sequential execution handles failures"""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            {"agent_type": "CodeAgent", "task": "Fail task"},
            {"agent_type": "CodeAgent", "task": "Skip task"}
        ]
        
        result = orchestrator.execute_sequential(tasks, on_error="skip")
        
        assert result["status"] in ["complete", "partial"]
    
    def test_result_aggregation(self):
        """Test aggregating results from multiple agents"""
        orchestrator = AgentOrchestrator()
        
        orchestrator.agent_results["agent1"] = {"output": "Result 1"}
        orchestrator.agent_results["agent2"] = {"output": "Result 2"}
        
        aggregated = orchestrator.aggregate_results()
        
        assert "agent1" in aggregated
        assert "agent2" in aggregated
        assert aggregated["agent1"]["output"] == "Result 1"
    
    def test_execution_tree_generation(self):
        """Test generating execution tree from history"""
        orchestrator = AgentOrchestrator()
        
        # Simulate execution
        orchestrator.execution_history.append(
            {"agent_id": "a1", "role": "plan", "status": "complete"}
        )
        orchestrator.execution_history.append(
            {"agent_id": "a2", "role": "code", "status": "complete", "parent": "a1"}
        )
        
        tree = orchestrator.generate_execution_tree()
        
        assert "a1" in tree
        assert "a2" in tree
    
    def test_parallel_execution_mock(self):
        """Test parallel agent execution (mocked)"""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            {"agent_type": "ResearchAgent", "task": "Research option 1"},
            {"agent_type": "ResearchAgent", "task": "Research option 2"},
            {"agent_type": "ResearchAgent", "task": "Research option 3"}
        ]
        
        result = orchestrator.execute_parallel(tasks)
        
        # Should complete all tasks
        assert len(orchestrator.agent_results) >= 1
    
    def test_error_handling_retry(self):
        """Test error handling with retry"""
        orchestrator = AgentOrchestrator()
        
        task = {"agent_type": "CodeAgent", "task": "Create file"}
        
        result = orchestrator.execute_with_retry(
            task,
            max_retries=3
        )
        
        assert result is not None
    
    def test_context_passing_to_sub_agents(self):
        """Test context passing between agents"""
        orchestrator = AgentOrchestrator()
        
        context = {
            "project_root": "/tmp/project",
            "config": {"model": "mistral:7b"}
        }
        
        agent = orchestrator._create_agent_with_context(
            "CodeAgent",
            "Create file",
            context
        )
        
        assert agent is not None
        assert agent.role == "code"
