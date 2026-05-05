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


def test_plan_writer_write_refined_plan():
    """Test writing refined plan content"""
    with tempfile.TemporaryDirectory() as tmpdir:
        refined_content = "# Refined Plan\n\n## New Section\nRefined content"
        
        writer = PlanWriter(output_dir=tmpdir)
        success, backup, filepath = writer.write_refined_plan(refined_content)
        
        assert success is True
        assert filepath.endswith("plan.md")
        assert os.path.exists(filepath)
        
        with open(filepath, "r") as f:
            content = f.read()
            assert content == refined_content


def test_plan_writer_write_refined_plan_creates_backup():
    """Test that writing refined plan creates backup of original"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "plan.md")
        
        # Create original plan
        with open(plan_path, "w") as f:
            f.write("# Original Plan\n\nOriginal content")
        
        # Write refined plan
        refined_content = "# Refined Plan\n\nRefined content"
        writer = PlanWriter(output_dir=tmpdir)
        success, backup, filepath = writer.write_refined_plan(refined_content, filepath=plan_path)
        
        assert success is True
        assert backup is not None
        assert os.path.exists(backup)
        
        # Verify backup has original content
        with open(backup, "r") as f:
            backup_content = f.read()
            assert "Original Plan" in backup_content
        
        # Verify plan has refined content
        with open(plan_path, "r") as f:
            plan_content = f.read()
            assert "Refined Plan" in plan_content


def test_plan_writer_write_refined_plan_no_backup_if_file_missing():
    """Test refined plan write when file doesn't exist yet"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "new_plan.md")
        
        refined_content = "# New Plan\n\nNew content"
        writer = PlanWriter(output_dir=tmpdir)
        success, backup, filepath = writer.write_refined_plan(refined_content, filepath=plan_path)
        
        assert success is True
        assert backup is None  # No backup since file didn't exist
        assert os.path.exists(filepath)
        
        with open(filepath, "r") as f:
            content = f.read()
            assert content == refined_content


def test_plan_writer_write_refined_plan_error_handling():
    """Test error handling in write_refined_plan"""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = PlanWriter(output_dir=tmpdir)
        
        # Try to write to a path with invalid parent directory
        invalid_path = "/root/invalid/nonexistent/path/plan.md"
        success, backup, error_msg = writer.write_refined_plan("content", filepath=invalid_path)
        
        assert success is False
        assert isinstance(error_msg, str)


def test_plan_writer_create_backup():
    """Test backup creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "plan.md")
        
        # Create original file
        with open(plan_path, "w") as f:
            f.write("Original content")
        
        writer = PlanWriter(output_dir=tmpdir)
        backup_path = writer._create_backup(plan_path)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert "backups" in backup_path
        
        with open(backup_path, "r") as f:
            content = f.read()
            assert content == "Original content"


def test_plan_writer_create_backup_nonexistent_file():
    """Test backup creation for nonexistent file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "nonexistent.md")
        
        writer = PlanWriter(output_dir=tmpdir)
        backup_path = writer._create_backup(plan_path)
        
        assert backup_path is None


def test_plan_writer_create_backup_multiple_times():
    """Test creating multiple backups"""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_path = os.path.join(tmpdir, "plan.md")
        
        # Create and backup first version
        with open(plan_path, "w") as f:
            f.write("Version 1")
        
        writer = PlanWriter(output_dir=tmpdir)
        backup1 = writer._create_backup(plan_path)
        
        # Update and backup second version
        import time
        time.sleep(1.01)  # Sleep long enough to get different second
        
        with open(plan_path, "w") as f:
            f.write("Version 2")
        
        backup2 = writer._create_backup(plan_path)
        
        # Both backups should exist
        assert os.path.exists(backup1)
        assert os.path.exists(backup2)
        
        # Backups should be different files (or same path but different content)
        # Verify content
        with open(backup1, "r") as f:
            content1 = f.read()
            assert content1 == "Version 1"
        
        with open(backup2, "r") as f:
            content2 = f.read()
            assert content2 == "Version 2"
        
        # Backups directory should exist
        backup_dir = os.path.dirname(backup1)
        assert os.path.exists(backup_dir)
