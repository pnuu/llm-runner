"""Tests for specialized agent types"""
import pytest
from llm_runner.agents.code_agent import CodeAgent
from llm_runner.agents.plan_agent import PlanAgent
from llm_runner.agents.research_agent import ResearchAgent
from llm_runner.agents.build_agent import BuildAgent


class TestCodeAgent:
    """Test CodeAgent specialization"""
    
    def test_code_agent_creation(self):
        """Test CodeAgent initialization"""
        agent = CodeAgent(task="Create API", llm_client=None)
        
        assert agent.role == "code"
        assert agent.task == "Create API"
        assert "coding" in agent.capabilities
    
    def test_code_agent_capabilities(self):
        """Test CodeAgent has expected capabilities"""
        agent = CodeAgent(task="Test", llm_client=None)
        
        assert "file_creation" in agent.capabilities
        assert "debugging" in agent.capabilities


class TestPlanAgent:
    """Test PlanAgent specialization"""
    
    def test_plan_agent_creation(self):
        """Test PlanAgent initialization"""
        agent = PlanAgent(task="Plan API", llm_client=None)
        
        assert agent.role == "plan"
        assert agent.task == "Plan API"
        assert "planning" in agent.capabilities
    
    def test_plan_agent_capabilities(self):
        """Test PlanAgent has expected capabilities"""
        agent = PlanAgent(task="Test", llm_client=None)
        
        assert "decomposition" in agent.capabilities
        assert "analysis" in agent.capabilities


class TestResearchAgent:
    """Test ResearchAgent specialization"""
    
    def test_research_agent_creation(self):
        """Test ResearchAgent initialization"""
        agent = ResearchAgent(task="Research topic", llm_client=None)
        
        assert agent.role == "research"
        assert "research" in agent.capabilities
    
    def test_research_agent_capabilities(self):
        """Test ResearchAgent has expected capabilities"""
        agent = ResearchAgent(task="Test", llm_client=None)
        
        assert "analysis" in agent.capabilities
        assert "summarization" in agent.capabilities


class TestBuildAgent:
    """Test BuildAgent specialization"""
    
    def test_build_agent_creation(self):
        """Test BuildAgent initialization"""
        agent = BuildAgent(task="Build project", llm_client=None)
        
        assert agent.role == "build"
        assert "execution" in agent.capabilities
    
    def test_build_agent_capabilities(self):
        """Test BuildAgent has expected capabilities"""
        agent = BuildAgent(task="Test", llm_client=None)
        
        assert "command_execution" in agent.capabilities
        assert "file_management" in agent.capabilities
