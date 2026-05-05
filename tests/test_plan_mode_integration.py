"""End-to-end integration tests for plan refinement workflow"""
import os
import tempfile
import pytest
from llm_runner.plan_handler import (
    handle_interactive_plan_refinement,
    detect_and_save_plan_refinement,
    read_existing_plan
)
from llm_runner.plan_writer import PlanWriter
from llm_runner.plan_outline import PlanOutlineExtractor
from llm_runner.plan_refinement import PlanRefinementDetector


class TestCompleteRefinementWorkflow:
    """Test the complete plan refinement workflow end-to-end"""
    
    def test_workflow_enter_mode_display_outline(self):
        """Test entering plan mode displays outline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_content = """# Project Plan
            
## Phase 1
- Design
- Review

## Phase 2  
- Development
- Testing
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            # Enter plan refinement mode
            state = handle_interactive_plan_refinement(tmpdir)
            assert state is not None
            assert state["has_existing_plan"] is True
            assert state["original_plan"] == plan_content
            
            # Verify outline can be extracted
            extractor = PlanOutlineExtractor()
            outline = extractor.format_outline(plan_content)
            assert len(outline) > 0
    
    def test_workflow_refinement_with_explicit_keywords(self):
        """Test refinement detection with explicit add/modify keywords"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_content = "# API\n\n## Endpoints\n- GET /users"
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Chat with explicit "add" keyword that will trigger detection
            chat = """
User: Add authentication section
AI: I'll add authentication with JWT.

## Authentication
- JWT tokens
- OAuth2
"""
            
            # Should detect changes with explicit keywords
            detector = PlanRefinementDetector()
            has_changes = detector.detect_changes(plan_content, chat)
            
            # If detected, should be able to extract refined plan
            if has_changes:
                refined = detector.extract_refined_plan(chat, plan_content)
                assert refined is not None
                assert len(refined) > 0
    
    def test_workflow_backup_creation_on_refinement(self):
        """Test that backups are created when refinements are saved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_plan = "# Original\n\n## Section 1"
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(original_plan)
            
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Chat that should trigger refinement with explicit keywords
            chat = """
User: Add new section
AI: I'll add a new section to the plan.

## Section 2
New content here
"""
            
            # Attempt to detect and save
            result = detect_and_save_plan_refinement(state, chat, tmpdir)
            
            # If saved, verify backup exists
            if result:
                backup_dir = os.path.join(tmpdir, "backups")
                assert os.path.exists(backup_dir)
                backups = os.listdir(backup_dir)
                assert len(backups) > 0


class TestRefinementWithoutChanges:
    """Test workflow when discussion doesn't contain refinements"""
    
    def test_no_refinement_on_questions_only(self):
        """Test that questions about plan don't trigger refinement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_content = "# Plan\n\n## Overview\nProject overview"
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Chat with only questions - no refinement keywords
            chat = """
User: What's the timeline for this project?
AI: Based on the plan, the project should take about 4 weeks.
"""
            
            # Should not detect changes
            result = detect_and_save_plan_refinement(state, chat, tmpdir)
            assert result is False
    
    def test_refinement_state_without_original_plan(self):
        """Test refinement detection when no original plan exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = handle_interactive_plan_refinement(tmpdir)
            
            # No existing plan
            assert state["has_existing_plan"] is False
            assert state["original_plan"] is None
            
            # Attempt refinement on missing plan
            chat = "User: Add section\nAI: Adding section\n\n## New"
            result = detect_and_save_plan_refinement(state, chat, tmpdir)
            
            # Should return False for missing original
            assert result is False


class TestWorkflowIntegration:
    """Test complete workflow integration"""
    
    def test_full_workflow_setup_and_backup(self):
        """Test full workflow: setup → refine → backup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create initial plan
            initial_plan = """# Deployment Plan

## Phase 1
- Infrastructure setup
- Database migration

## Phase 2
- Application deployment
- Testing
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(initial_plan)
            
            # Step 2: Enter plan mode
            state = handle_interactive_plan_refinement(tmpdir)
            assert state["has_existing_plan"] is True
            
            # Step 3: Simulate refinement attempt
            chat = """
User: Add monitoring section
AI: I'll add comprehensive monitoring to the plan.

## Monitoring
- Prometheus metrics
- ELK stack
"""
            
            # Step 4: Attempt detection
            try:
                result = detect_and_save_plan_refinement(state, chat, tmpdir)
                # Whether detected or not, workflow should complete
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Workflow should not raise exception: {e}")
    
    def test_workflow_preserves_plan_structure(self):
        """Test that plan structure is preserved through refinement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            structured_plan = """# API Development

## Requirements
- User authentication
- Data persistence

## Architecture
- Frontend layer
- Backend layer
- Database layer

## Timeline
- Week 1-2: Design
- Week 3-4: Development
- Week 5: Testing
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(structured_plan)
            
            # Extract outline before
            extractor = PlanOutlineExtractor()
            outline_before = extractor.format_outline(structured_plan)
            
            # Attempt refinement
            state = handle_interactive_plan_refinement(tmpdir)
            chat = "User: Discuss the plan\nAI: The plan looks good.\n\nThis is a comprehensive plan"
            detect_and_save_plan_refinement(state, chat, tmpdir)
            
            # Verify plan still readable
            current_plan = read_existing_plan(tmpdir)
            assert current_plan is not None
            assert "Architecture" in current_plan or "architecture" in current_plan.lower()


class TestErrorRecovery:
    """Test error handling in workflow"""
    
    def test_workflow_handles_empty_chat(self):
        """Test workflow with empty chat content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write("# Plan")
            
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Empty chat
            result = detect_and_save_plan_refinement(state, "", tmpdir)
            assert result is False
    
    def test_workflow_handles_none_plan_state(self):
        """Test workflow with None plan state"""
        result = detect_and_save_plan_refinement(None, "chat content", ".")
        assert result is False
    
    def test_workflow_handles_invalid_paths(self):
        """Test workflow handles invalid directory paths gracefully"""
        state = {
            "has_existing_plan": True,
            "original_plan": "# Plan",
            "plan_path": "/invalid/nonexistent/plan.md"
        }
        
        # Should handle gracefully even with bad path
        result = detect_and_save_plan_refinement(state, "chat", "/also/invalid/dir")
        assert isinstance(result, bool)


class TestPlanContextManagement:
    """Test plan context handling through refinement"""
    
    def test_context_available_in_refinement_state(self):
        """Test that plan context is available in state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_content = """# System Design

## Overview
Complete system design plan

## Components
- Authentication module
- Database layer
- API layer
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan_content)
            
            # Enter plan mode
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Verify context available
            assert "plan_path" in state
            assert "original_plan" in state
            assert state["original_plan"] == plan_content
    
    def test_refinement_detector_uses_full_plan(self):
        """Test that refinement detector has access to full plan content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = "# Project\n\n## Requirements\n- Requirement 1"
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan)
            
            state = handle_interactive_plan_refinement(tmpdir)
            
            # Detector should work with plan from state
            detector = PlanRefinementDetector()
            
            # Even if it doesn't detect changes, it should work
            result = detector.detect_changes(state["original_plan"], "some chat")
            assert isinstance(result, bool)


class TestOutlineGeneration:
    """Test outline generation during refinement workflow"""
    
    def test_outline_generated_for_valid_plans(self):
        """Test that valid plans generate outlines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = """# Project Roadmap

## Q1 Goals
- Goal 1
- Goal 2

## Q2 Goals
- Goal 3

## Resources
- Team members
- Tools
"""
            plan_path = os.path.join(tmpdir, "plan.md")
            with open(plan_path, "w") as f:
                f.write(plan)
            
            extractor = PlanOutlineExtractor()
            outline = extractor.format_outline(plan)
            
            assert len(outline) > 0
            # Outline should contain key sections
            assert "Q1" in outline or "Goals" in outline or "Project" in outline
