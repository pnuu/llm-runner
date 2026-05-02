"""Test plan file writing"""
import os
import tempfile
from datetime import datetime
from llm_runner.planner import Plan
from llm_runner.plan_writer import PlanWriter


def test_plan_writer_init():
    """Test PlanWriter initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = PlanWriter(output_dir=tmpdir)
        assert writer.output_dir == tmpdir


def test_plan_writer_write_plan():
    """Test writing plan to file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan = Plan(
            title="Test Plan",
            approach="Test approach",
            steps=["Step 1", "Step 2"],
            notes="Test notes"
        )
        
        writer = PlanWriter(output_dir=tmpdir)
        filepath = writer.write_plan(plan, request="Test request")
        
        assert os.path.exists(filepath)
        assert filepath.endswith("plan.md")
        
        with open(filepath, "r") as f:
            content = f.read()
            assert "Test Plan" in content
            assert "Test approach" in content
            assert "Step 1" in content


def test_plan_writer_includes_metadata():
    """Test that written plan includes metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan = Plan(
            title="API Plan",
            approach="REST approach",
            steps=["Create endpoints"],
            notes="None"
        )
        
        writer = PlanWriter(output_dir=tmpdir)
        filepath = writer.write_plan(plan, request="Create REST API")
        
        with open(filepath, "r") as f:
            content = f.read()
            # Should include the original request
            assert "Create REST API" in content or "Request" in content


def test_plan_writer_different_directories():
    """Test writing to different directories"""
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            plan = Plan("Test", "Test", ["Step"], "Note")
            
            writer1 = PlanWriter(output_dir=tmpdir1)
            path1 = writer1.write_plan(plan)
            
            writer2 = PlanWriter(output_dir=tmpdir2)
            path2 = writer2.write_plan(plan)
            
            assert os.path.dirname(path1) == tmpdir1
            assert os.path.dirname(path2) == tmpdir2
            assert path1 != path2


def test_plan_writer_handles_existing_file():
    """Test that writer handles existing plan.md files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an existing plan.md
        existing_file = os.path.join(tmpdir, "plan.md")
        with open(existing_file, "w") as f:
            f.write("Old plan")
        
        plan = Plan("New Plan", "New", ["New Step"], "")
        writer = PlanWriter(output_dir=tmpdir)
        
        # Should either overwrite or create a backup
        filepath = writer.write_plan(plan)
        assert os.path.exists(filepath)
        
        with open(filepath, "r") as f:
            content = f.read()
            assert "New Plan" in content
