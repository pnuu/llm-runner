"""Test plan generation module"""
from unittest.mock import patch, MagicMock
import pytest
from llm_runner.planner import PlanGenerator, Plan


def test_plan_object_creation():
    """Test Plan object creation"""
    plan = Plan(
        title="Create REST API",
        approach="Use Flask framework",
        steps=["Step 1", "Step 2"],
        notes="Important: use blueprints"
    )
    assert plan.title == "Create REST API"
    assert plan.approach == "Use Flask framework"
    assert len(plan.steps) == 2
    assert "blueprints" in plan.notes


def test_plan_to_markdown():
    """Test converting plan to markdown"""
    plan = Plan(
        title="Build CLI",
        approach="Modular design",
        steps=["Create parser", "Add subcommands"],
        notes="Keep it simple"
    )
    md = plan.to_markdown()
    assert "# Build CLI" in md
    assert "Modular design" in md
    assert "Create parser" in md


def test_plan_generator_init():
    """Test PlanGenerator initialization"""
    with patch("llm_runner.planner.OllamaClient"):
        with patch("llm_runner.planner.check_ollama_connection", return_value=True):
            gen = PlanGenerator(
                ollama_url="http://localhost:11434",
                model="mistral:7b"
            )
            assert gen.model == "mistral:7b"


def test_plan_generator_connection_check():
    """Test PlanGenerator checks connection"""
    with patch("llm_runner.planner.check_ollama_connection", return_value=False):
        with pytest.raises(Exception):
            PlanGenerator()


def test_plan_generator_generate_plan():
    """Test generating a plan from request"""
    with patch("llm_runner.planner.OllamaClient") as mock_client_class:
        with patch("llm_runner.planner.check_ollama_connection", return_value=True):
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = """
Title: Create API
Approach: Use REST principles
Steps:
- Define endpoints
- Implement handlers
- Add tests
Notes: Start simple
"""
            mock_client_class.return_value = mock_client
            
            gen = PlanGenerator()
            plan = gen.generate_plan("Create a REST API")
            
            assert isinstance(plan, Plan)
            assert plan.title is not None


def test_plan_generator_with_context():
    """Test plan generation with additional context"""
    with patch("llm_runner.planner.OllamaClient") as mock_client_class:
        with patch("llm_runner.planner.check_ollama_connection", return_value=True):
            mock_client = MagicMock()
            mock_client.send_prompt.return_value = "Title: Test\nApproach: Test\nSteps:\nNotes: None"
            mock_client_class.return_value = mock_client
            
            gen = PlanGenerator()
            context = "Use TDD methodology"
            plan = gen.generate_plan("Test", context=context)
            
            # Verify context was included in the prompt
            call_args = mock_client.send_prompt.call_args
            assert context in call_args[0][0] or context in str(call_args)
