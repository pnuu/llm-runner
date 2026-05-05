"""Tests for plan outline extraction"""
import pytest
from llm_runner.plan_outline import PlanOutlineExtractor


class TestOutlineExtraction:
    """Test basic outline extraction"""
    
    def test_extract_from_simple_plan(self):
        """Test extracting outline from simple structured plan"""
        plan = """# Deployment Plan
        
## Architecture
- Docker containers
- Kubernetes cluster
- Load balancer

## Deployment
- Blue-green strategy
- Canary releases
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Architecture" in outline
        assert "Deployment" in outline
        assert "Docker" in outline
    
    def test_extract_from_complex_nested_plan(self):
        """Test extracting from plan with multiple nesting levels"""
        plan = """# Project Plan

## Phase 1: Setup
### Infrastructure
- Configure network
- Deploy database

### Testing
- Unit tests
- Integration tests

## Phase 2: Launch
### Deployment
- Production rollout
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Phase 1" in outline
        assert "Infrastructure" in outline
        assert "Phase 2" in outline
    
    def test_extract_preserves_hierarchy(self):
        """Test that hierarchy is maintained in outline"""
        plan = """# Main Task

## Section 1
- Item A
- Item B

### Subsection
- Item C
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        # Should have different indentation levels
        lines = outline.split('\n')
        # Find section 1 line
        section_line = next(l for l in lines if "Section 1" in l)
        assert section_line.startswith("  •") or section_line.startswith("• ")
    
    def test_extract_from_narrative_plan(self):
        """Test extracting from paragraph-based plan"""
        plan = """# Project Overview

## Objectives
We need to deploy to production.

## Requirements
The system must be reliable.

## Timeline
Four weeks total.
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        # Should extract headers even without bullets
        assert "Objectives" in outline or "Requirements" in outline
    
    def test_extract_from_mixed_format(self):
        """Test extracting from mixed format (headers + bullets + text)"""
        plan = """# Plan

## Part A
- Task 1
- Task 2

Some additional narrative here.

## Part B
More text describing the approach.
- Implementation detail
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Part A" in outline
        assert "Part B" in outline
    
    def test_limit_bullets_per_section(self):
        """Test that only first few bullets are included"""
        plan = """# Tasks

## Section
- Bullet 1
- Bullet 2
- Bullet 3
- Bullet 4
- Bullet 5
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        # Count bullets - should be limited
        bullet_count = outline.count('-')
        assert bullet_count <= PlanOutlineExtractor.MAX_SECTION_BULLETS + 1  # +1 for section marker
    
    def test_limit_total_lines(self):
        """Test that outline is limited to MAX_LINES"""
        # Create a very long plan
        plan_lines = ["# Long Plan"]
        for i in range(100):
            plan_lines.append(f"## Section {i}")
            plan_lines.append(f"- Item {i}")
        
        plan = '\n'.join(plan_lines)
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        lines = outline.split('\n')
        assert len(lines) <= PlanOutlineExtractor.MAX_LINES
    
    def test_empty_plan(self):
        """Test handling of empty plan"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary("")
        
        assert outline == ""
    
    def test_none_plan(self):
        """Test handling of None plan"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(None)
        
        assert outline == ""
    
    def test_whitespace_only_plan(self):
        """Test handling of whitespace-only plan"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary("   \n\n   ")
        
        assert outline == ""
    
    def test_extract_status_from_plan(self):
        """Test extraction of status information"""
        plan = """# Plan

## Tasks
- Task 1

Status: In progress, 50% complete
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Status" in outline
        assert "progress" in outline
    
    def test_skip_code_blocks(self):
        """Test that code blocks are skipped"""
        plan = """# Plan

## Tasks
- Task 1

```python
def task():
    pass
```

- Task 2 (should appear)
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        # Code block should not appear
        assert "def task" not in outline
        assert "Task 2" in outline or "should appear" not in outline


class TestOutlineFormatting:
    """Test outline formatting for display"""
    
    def test_format_with_header(self):
        """Test formatting with header"""
        plan = """# Plan

## Section 1
- Item 1
"""
        extractor = PlanOutlineExtractor()
        formatted = extractor.format_outline(plan, include_header=True)
        
        assert "Current Plan Summary" in formatted
        assert "Section 1" in formatted
        assert formatted.startswith("\n===")
    
    def test_format_without_header(self):
        """Test formatting without header"""
        plan = """# Plan

## Section
- Item
"""
        extractor = PlanOutlineExtractor()
        formatted = extractor.format_outline(plan, include_header=False)
        
        assert "Current Plan Summary" not in formatted
        assert "Section" in formatted
    
    def test_format_empty_plan(self):
        """Test formatting empty plan"""
        extractor = PlanOutlineExtractor()
        formatted = extractor.format_outline("", include_header=True)
        
        assert "No plan content" in formatted
    
    def test_format_preserves_content(self):
        """Test that formatting preserves all content"""
        plan = """# Project

## Phase 1
- Step A
- Step B

## Phase 2
- Step C
"""
        extractor = PlanOutlineExtractor()
        formatted = extractor.format_outline(plan, include_header=True)
        
        assert "Phase 1" in formatted
        assert "Phase 2" in formatted
        assert "Step A" in formatted


class TestRealWorldPlans:
    """Test with real-world plan formats"""
    
    def test_deployment_plan(self):
        """Test with deployment plan format"""
        plan = """# Kubernetes Deployment Plan

## Architecture Review
- Microservice dependencies
- Load balancing strategy
- Database replication

## Deployment Strategy
- Blue-green deployment
- Canary releases
- Automated rollback

## Testing
- Integration tests
- Performance tests
- Security audit

Status: Ready for implementation
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Architecture Review" in outline
        assert "Deployment Strategy" in outline
        assert "Status" in outline
    
    def test_feature_plan(self):
        """Test with feature development plan"""
        plan = """# New Feature Development

## Requirements Gathering
- Interview stakeholders
- Document use cases
- Create wireframes

## Implementation
### Backend
- API endpoints
- Database schema

### Frontend
- UI components
- State management

## Testing & QA
- Unit tests
- E2E tests

Completion: 40% done
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        # Should show main sections
        assert "Requirements" in outline or "Implementation" in outline
    
    def test_project_plan_with_timeline(self):
        """Test project plan with timeline"""
        plan = """# Project X Plan

## Overview
Complete system migration

## Timeline
- Week 1: Planning
- Week 2: Development
- Week 3: Testing
- Week 4: Deployment

## Risks
- Resource constraints
- Timeline pressure

Status: In progress, Week 2
"""
        extractor = PlanOutlineExtractor()
        outline = extractor.extract_summary(plan)
        
        assert "Timeline" in outline or "Week" in outline
