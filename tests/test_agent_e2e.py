"""End-to-end tests for agent system workflows"""
from unittest.mock import MagicMock, patch
from llm_runner.agent_orchestrator import AgentOrchestrator
from llm_runner.agents.plan_agent import PlanAgent


class TestAgentE2E:
    """Test complete agent workflows"""
    
    def test_simple_task_delegation(self):
        """Test simple sequential delegation"""
        tasks = [
            {"agent_type": "PlanAgent", "task": "Plan feature"},
            {"agent_type": "CodeAgent", "task": "Implement feature"},
        ]
        
        orchestrator = AgentOrchestrator()
        result = orchestrator.execute_sequential(tasks)
        
        assert result["status"] == "complete"
        assert result["tasks_completed"] == 2
    
    def test_task_with_error_skip(self):
        """Test task execution with error skip strategy"""
        tasks = [
            {"agent_type": "CodeAgent", "task": "Succeed"},
            {"agent_type": "CodeAgent", "task": "Fail silently"},
            {"agent_type": "CodeAgent", "task": "Succeed after error"},
        ]
        
        orchestrator = AgentOrchestrator()
        result = orchestrator.execute_sequential(tasks, on_error="skip")
        
        assert result["status"] == "complete"
        assert len(orchestrator.execution_history) == 3
    
    def test_parallel_research_tasks(self):
        """Test parallel agent execution for independent research"""
        tasks = [
            {"agent_type": "ResearchAgent", "task": "Research tech A"},
            {"agent_type": "ResearchAgent", "task": "Research tech B"},
            {"agent_type": "ResearchAgent", "task": "Research tech C"},
        ]
        
        orchestrator = AgentOrchestrator()
        result = orchestrator.execute_parallel(tasks)
        
        assert result["status"] == "complete"
        assert len(orchestrator.agent_results) >= 1
    
    def test_result_aggregation_across_agents(self):
        """Test aggregating results from multiple agents"""
        orchestrator = AgentOrchestrator()
        
        tasks = [
            {"agent_type": "PlanAgent", "task": "Task 1"},
            {"agent_type": "CodeAgent", "task": "Task 2"},
        ]
        
        orchestrator.execute_sequential(tasks)
        aggregated = orchestrator.aggregate_results()
        
        # Should have results from both agents
        assert len(aggregated) > 0
    
    def test_complex_decomposition_workflow(self):
        """Test complex task decomposition and execution"""
        mock_llm = MagicMock()
        mock_llm.send_prompt.return_value = """
Sub-tasks:
1. PlanAgent: Design system
2. CodeAgent: Implement core
3. TestAgent: Test implementation
"""
        
        planner = PlanAgent(task="Build system", llm_client=mock_llm)
        decomposition = planner.decompose_task()
        
        assert "PlanAgent" in decomposition
        assert "CodeAgent" in decomposition
        assert "TestAgent" in decomposition
