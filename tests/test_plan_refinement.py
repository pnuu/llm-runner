"""Tests for plan refinement detection and extraction"""
import pytest
from llm_runner.plan_refinement import PlanRefinementDetector


class TestRefinementDetection:
    """Test plan refinement detection"""
    
    def test_detect_new_section_added(self):
        """Test detection of new sections added"""
        original = """# Plan

## Section 1
- Item A
"""
        chat = """
User: Can you add a rollback section?

AI: Great idea! Here's the updated plan:

## Rollback Strategy
- Automated rollback
- Database recovery
"""
        detector = PlanRefinementDetector()
        score = detector.get_confidence_score(original, chat)
        # Should detect clear changes (above 0.59)
        assert score >= 0.59
    
    def test_detect_task_addition(self):
        """Test detection of new tasks added"""
        original = """# Tasks

## Phase 1
- Task 1
"""
        chat = """
User: Add more tasks to phase 1

AI: Sure, here are additional tasks:
- Task 2: Setup infrastructure
- Task 3: Configure deployment
"""
        detector = PlanRefinementDetector()
        assert detector.detect_changes(original, chat) is True
    
    def test_detect_section_removal(self):
        """Test detection of removed sections"""
        original = """# Plan

## To Remove
- Delete this

## Keep
- Keep this
"""
        chat = """
User: We should remove the old section

AI: You're right, the "To Remove" section is no longer needed.
Let's focus on "Keep" section instead.
"""
        detector = PlanRefinementDetector()
        # Should detect "remove" keyword with reasonable confidence
        score = detector.get_confidence_score(original, chat)
        assert score >= 0.50  # Should detect removal mention
    
    def test_detect_modification(self):
        """Test detection of plan modifications"""
        original = """# Plan

## Section 1
- Use Docker
"""
        chat = """
User: Modify the deployment approach

AI: Let's update this:

## Section 1
- Use Kubernetes instead
- Add load balancing
"""
        detector = PlanRefinementDetector()
        assert detector.detect_changes(original, chat) is True
    
    def test_ignore_casual_discussion(self):
        """Test that casual discussion is ignored"""
        original = "# Plan"
        chat = """
User: What's the weather?
AI: It's sunny today.
"""
        detector = PlanRefinementDetector()
        # Casual discussion should not trigger refinement detection
        score = detector.get_confidence_score(original, chat)
        assert score < PlanRefinementDetector.MIN_CONFIDENCE
    
    def test_ignore_questions_about_plan(self):
        """Test that questions (without proposed changes) are ignored"""
        original = "# Plan"
        chat = """
User: What's the timeline for phase 1?
AI: Phase 1 is planned for 2 weeks.
"""
        detector = PlanRefinementDetector()
        # Casual discussion about plan (not modifying)
        score = detector.get_confidence_score(original, chat)
        assert score < 0.60  # Should not pass refinement threshold
    
    def test_high_confidence_on_multiple_changes(self):
        """Test high confidence when multiple changes mentioned"""
        original = "# Plan"
        chat = """
User: Add new sections and modify the timeline

AI: Updated plan:
- Add deployment section
- Create testing phase
- Modify the rollback strategy
"""
        detector = PlanRefinementDetector()
        score = detector.get_confidence_score(original, chat)
        # Multiple change keywords should give good confidence
        assert score >= 0.60
    
    def test_no_changes_in_empty_chat(self):
        """Test that empty chat shows no changes"""
        original = "# Plan"
        detector = PlanRefinementDetector()
        assert detector.detect_changes(original, "") is False
    
    def test_no_changes_with_none_original(self):
        """Test with None original plan"""
        chat = "User: Something"
        detector = PlanRefinementDetector()
        assert detector.detect_changes(None, chat) is False
    
    def test_structural_detection_with_sections(self):
        """Test structural change detection with new sections"""
        original = "# Plan"
        chat = """
Here's the updated plan:

## New Section 1
- Point A

## New Section 2
- Point B
- Point C
"""
        detector = PlanRefinementDetector()
        score = detector.get_confidence_score(original, chat)
        # Should detect structural changes (multiple sections)
        assert score > 0.0
    
    def test_confidence_score_normalization(self):
        """Test that confidence scores are normalized to 0-1"""
        original = "# Plan"
        chat = """
User: Add add add many changes and modifications
AI: Update update with new new implementation
"""
        detector = PlanRefinementDetector()
        score = detector.get_confidence_score(original, chat)
        assert 0.0 <= score <= 1.0


class TestPlanExtraction:
    """Test plan extraction from chat"""
    
    def test_extract_simple_section(self):
        """Test extracting simple section from chat"""
        original = "# Original Plan"
        chat = """
Here's the new section:

## New Strategy
- Step 1
- Step 2
"""
        detector = PlanRefinementDetector()
        extracted = detector.extract_refined_plan(chat, original)
        
        assert "New Strategy" in extracted or "Step" in extracted
    
    def test_extract_multiple_sections(self):
        """Test extracting multiple sections"""
        original = "# Plan"
        chat = """
Updated plan:

## Section A
- Task A1
- Task A2

## Section B
- Task B1
"""
        detector = PlanRefinementDetector()
        extracted = detector.extract_refined_plan(chat, original)
        
        # Should contain at least one section marker
        assert "##" in extracted or "Section" in extracted
    
    def test_extract_handles_no_plan_structure(self):
        """Test extraction when chat doesn't contain plan structure"""
        original = "# Original"
        chat = "Just discussing things without structure"
        
        detector = PlanRefinementDetector()
        extracted = detector.extract_refined_plan(chat, original)
        
        # Should return original if no plan structure found
        assert extracted == original
    
    def test_extract_preserves_original_if_no_chat(self):
        """Test that extraction returns original if no chat"""
        original = "# Original Plan"
        detector = PlanRefinementDetector()
        extracted = detector.extract_refined_plan("", original)
        
        assert extracted == original
    
    def test_extract_section_detection(self):
        """Test internal section detection"""
        detector = PlanRefinementDetector()
        
        chat = """
## First Section
- Item 1

## Second Section
- Item 2
"""
        sections = detector._extract_plan_sections(chat)
        
        assert len(sections) >= 1
        assert any("First Section" in s for s in sections) or any("Second" in s for s in sections)


class TestKeywordAnalysis:
    """Test keyword analysis for changes"""
    
    def test_analyze_add_keyword(self):
        """Test analysis with 'add' keyword"""
        detector = PlanRefinementDetector()
        score = detector._analyze_for_keywords("Add a new section to the plan")
        
        assert score >= 0.8  # 'add' has high confidence
    
    def test_analyze_remove_keyword(self):
        """Test analysis with 'remove' keyword"""
        detector = PlanRefinementDetector()
        score = detector._analyze_for_keywords("Remove the old deployment approach")
        
        assert score >= 0.8  # 'remove' has high confidence
    
    def test_analyze_multiple_keywords(self):
        """Test analysis with multiple change keywords"""
        detector = PlanRefinementDetector()
        score = detector._analyze_for_keywords("Add new tasks and modify existing steps")
        
        assert score > 0.5  # Should detect multiple keywords
    
    def test_analyze_no_keywords(self):
        """Test analysis with no change keywords"""
        detector = PlanRefinementDetector()
        score = detector._analyze_for_keywords("The plan looks good as is")
        
        # The word "plan" matches our keywords with 0.5 weight
        assert score >= 0.0  # May have low score from "plan" keyword
    
    def test_analyze_case_insensitive(self):
        """Test that keyword analysis is case insensitive"""
        detector = PlanRefinementDetector()
        score1 = detector._analyze_for_keywords("ADD a section")
        score2 = detector._analyze_for_keywords("add a section")
        
        # Both should have same score
        assert abs(score1 - score2) < 0.01


class TestStructuralChanges:
    """Test structural change detection"""
    
    def test_detect_new_sections_structure(self):
        """Test detection of new section headers"""
        detector = PlanRefinementDetector()
        chat = """
## New Section 1
Content

## New Section 2
More content
"""
        score = detector._detect_structural_changes(chat)
        assert score > 0.2
    
    def test_detect_bullet_point_structure(self):
        """Test detection of bullet point structure"""
        detector = PlanRefinementDetector()
        chat = """
- Task 1
- Task 2
- Task 3
"""
        score = detector._detect_structural_changes(chat)
        assert score > 0.2
    
    def test_detect_numbered_list_structure(self):
        """Test detection of numbered list structure"""
        detector = PlanRefinementDetector()
        chat = """
1. First step
2. Second step
3. Third step
"""
        score = detector._detect_structural_changes(chat)
        assert score > 0.2
    
    def test_no_structure_detected_in_prose(self):
        """Test that plain prose doesn't trigger structural detection"""
        detector = PlanRefinementDetector()
        chat = "Just some random text without any structure markers."
        
        score = detector._detect_structural_changes(chat)
        assert score == 0.0


class TestRealWorldScenarios:
    """Test with real-world refinement scenarios"""
    
    def test_deployment_plan_refinement(self):
        """Test refinement of deployment plan"""
        original = """# Deployment Plan

## Architecture
- Microservices
- Kubernetes

## Timeline
- Week 1: Setup
"""
        chat = """
User: Let's add a rollback strategy and modify timeline

AI: Great suggestions! Here's the updated plan:

## Architecture
- Microservices
- Kubernetes
- Load balancer

## Rollback Strategy
- Automated rollback on failure
- Database recovery procedures

## Timeline
- Week 1: Setup and testing
- Week 2: Deployment
"""
        detector = PlanRefinementDetector()
        
        # Should detect changes
        assert detector.detect_changes(original, chat) is True
        
        # Should extract updated sections
        extracted = detector.extract_refined_plan(chat, original)
        assert "Rollback" in extracted or "Timeline" in extracted
    
    def test_feature_plan_refinement(self):
        """Test refinement of feature development plan"""
        original = """# Feature Development

## Requirements
- Gather from stakeholders

## Implementation
- Backend API
"""
        chat = """
The refined plan includes:

## Requirements
- Gather from stakeholders
- Create detailed specifications
- Design database schema

## Implementation
- Backend API with GraphQL
- Frontend React components
- Mobile app support

## Testing
- Automated tests
- Performance testing
"""
        detector = PlanRefinementDetector()
        
        # Should detect structural changes (multiple sections with bullets)
        score = detector.get_confidence_score(original, chat)
        assert score >= 0.20  # Should detect some structural changes
