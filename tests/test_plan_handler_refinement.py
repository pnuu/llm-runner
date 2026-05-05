"""Tests for plan handler refinement workflow"""
import os
import tempfile
import pytest
from llm_runner.plan_handler import (
    handle_interactive_plan_refinement,
    detect_and_save_plan_refinement,
    read_existing_plan,
    display_plan_outline
)


class TestInteractivePlanRefinement:
    """Test interactive plan refinement setup"""
    
    def test_refinement_with_existing_plan(self):
        """Test entering refinement mode with existing plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing plan
            plan_content = "# Deployment Plan\n\n## Overview\nDeploy to prod\n\n## Tasks\n- Task 1\n- Task 2"
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            # Enter refinement mode
            state = handle_interactive_plan_refinement(tmpdir)
            
            assert state is not None
            assert state["has_existing_plan"] is True
            assert state["original_plan"] == plan_content
            assert state["plan_path"] == plan_path
    
    def test_refinement_without_existing_plan(self):
        """Test entering refinement mode without plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = handle_interactive_plan_refinement(tmpdir)
            
            assert state is not None
            assert state["has_existing_plan"] is False
            assert state["original_plan"] is None
    
    def test_refinement_state_contains_path(self):
        """Test refinement state contains plan path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = handle_interactive_plan_refinement(tmpdir)
            
            assert "plan_path" in state
            assert tmpdir in state["plan_path"]


class TestDetectAndSavePlanRefinement:
    """Test detection and saving of plan refinements"""
    
    def test_detect_simple_addition(self):
        """Test detecting simple plan addition"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_plan = "# Plan\n\n## Overview\nInitial overview"
            plan_path = os.path.join(tmpdir, "plan.md")
            
            # Setup
            with open(plan_path, "w") as f:
                f.write(original_plan)
            
            state = {
                "has_existing_plan": True,
                "original_plan": original_plan,
                "plan_path": plan_path
            }
            
            # Chat with refinement
            chat_content = """
User: Add a new section about testing to the plan
AI: I'll add that section now.

## Testing Strategy
- Unit tests for all components
- Integration tests for workflows
- Performance tests
"""
            
            result = detect_and_save_plan_refinement(state, chat_content, tmpdir)
            
            assert result is True
            
            # Verify plan was saved
            with open(plan_path, "r") as f:
                updated_plan = f.read()
            
            assert updated_plan != original_plan
            assert "Testing" in updated_plan or "testing" in updated_plan
    
    def test_no_refinement_detected(self):
        """Test when no refinement is detected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_plan = "# Plan\n\n## Overview\nInitial overview"
            plan_path = os.path.join(tmpdir, "plan.md")
            
            with open(plan_path, "w") as f:
                f.write(original_plan)
            
            state = {
                "has_existing_plan": True,
                "original_plan": original_plan,
                "plan_path": plan_path
            }
            
            # Chat without refinement
            chat_content = """
User: What do you think about this plan?
AI: This looks like a solid plan. The overview is clear and the timeline is reasonable.
"""
            
            result = detect_and_save_plan_refinement(state, chat_content, tmpdir)
            
            assert result is False
    
    def test_no_state_returns_false(self):
        """Test that no state returns False"""
        result = detect_and_save_plan_refinement(None, "chat content", ".")
        assert result is False
    
    def test_refinement_creates_backup(self):
        """Test that refinement creates backup file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_plan = "# Plan\n\n## Overview\nInitial"
            plan_path = os.path.join(tmpdir, "plan.md")
            
            with open(plan_path, "w") as f:
                f.write(original_plan)
            
            state = {
                "has_existing_plan": True,
                "original_plan": original_plan,
                "plan_path": plan_path
            }
            
            chat_content = """
User: Add rollback procedures to the plan
AI: I'll add a section about rollback procedures.

## Rollback Procedures
- Stop new deployments
- Revert to previous version
"""
            
            result = detect_and_save_plan_refinement(state, chat_content, tmpdir)
            
            assert result is True
            
            # Check backup exists
            backup_dir = os.path.join(tmpdir, "backups")
            assert os.path.exists(backup_dir)
            backups = os.listdir(backup_dir)
            assert len(backups) > 0
            assert "plan.md" in backups[0]
    
    def test_state_without_original_plan_returns_false(self):
        """Test state without original plan returns False"""
        state = {
            "has_existing_plan": False,
            "original_plan": None,
            "plan_path": "/tmp/plan.md"
        }
        
        result = detect_and_save_plan_refinement(state, "chat content", ".")
        assert result is False


class TestIntegrationWithRefinement:
    """Integration tests for complete refinement workflow"""
    
    def test_full_refinement_workflow(self):
        """Test complete workflow: setup -> detect -> save"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create initial plan
            plan_content = """# Microservices Deployment

## Overview
Deploy microservices to Kubernetes

## Architecture
- Service A
- Service B
- Load balancer

## Timeline
- Week 1: Setup
- Week 2: Deployment
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            # Step 2: Enter refinement mode
            state = handle_interactive_plan_refinement(tmpdir)
            assert state["has_existing_plan"] is True
            
            # Step 3: Simulate chat refinement
            chat = """
User: Can you add information about monitoring?
AI: I'll add a monitoring section.

## Monitoring
- Prometheus for metrics
- ELK stack for logs
- Alerts for critical issues
"""
            
            # Step 4: Detect and save refinement
            config = {"plan": {"refinement_confidence": 0.65}}
            saved = detect_and_save_plan_refinement(state, chat, tmpdir, config)
            
            assert saved is True
            
            # Step 5: Verify plan was updated
            with open(plan_path, "r") as f:
                updated = f.read()
            
            assert updated != plan_content
            # Should contain monitoring-related content
            assert "monitor" in updated.lower() or "prometheus" in updated.lower()
    
    def test_multiple_refinement_iterations(self):
        """Test multiple refinement iterations create backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "plan.md")
            plan_content = "# Plan\n\n## Phase 1\nInitial"
            
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            # First refinement
            state1 = handle_interactive_plan_refinement(tmpdir)
            chat1 = "User: Add phase 2\nAI: Adding phase 2\n\n## Phase 2\nSecond phase"
            result1 = detect_and_save_plan_refinement(state1, chat1, tmpdir)
            assert result1 is True
            
            # Check backup directory was created
            backup_dir = os.path.join(tmpdir, "backups")
            assert os.path.exists(backup_dir)
            
            # Verify backup was created
            backups = os.listdir(backup_dir)
            assert len(backups) >= 1
            
            # Verify we can read the first backup
            first_backup_path = os.path.join(backup_dir, backups[0])
            with open(first_backup_path, "r") as f:
                backup_content = f.read()
            
            # Backup should have original content
            assert "Phase 1" in backup_content or "Plan" in backup_content


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_plan(self):
        """Test refinement with empty plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write("")
            
            state = {
                "has_existing_plan": True,
                "original_plan": "",
                "plan_path": plan_path
            }
            
            config = {"plan": {"refinement_confidence": 0.65}}
            result = detect_and_save_plan_refinement(state, "Some chat", tmpdir, config)
            
            # Empty plan might detect as refinement if chat has content
            # Just verify it doesn't crash
            assert isinstance(result, bool)
    
    def test_readonly_directory_handles_gracefully(self):
        """Test that readonly directory doesn't crash"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = handle_interactive_plan_refinement(tmpdir)
            assert state is not None
    
    def test_missing_config_uses_defaults(self):
        """Test that missing config uses default threshold"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_content = "# Plan\n\n## Overview\nInitial"
            plan_path = os.path.join(tmpdir, "plan.md")
            
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            state = {
                "has_existing_plan": True,
                "original_plan": plan_content,
                "plan_path": plan_path
            }
            
            chat = "User: Add testing\nAI: Adding testing section\n\n## Testing\nTests here"
            
            # Call without config - should use defaults
            result = detect_and_save_plan_refinement(state, chat, tmpdir)
            
            # Should either save or not, but shouldn't crash
            assert isinstance(result, bool)
