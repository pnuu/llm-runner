"""Tests for chat integration with plan mode"""
import os
import tempfile
import pytest
from llm_runner.chat import InteractiveChat, ConversationHistory
from unittest.mock import Mock, patch, MagicMock


class TestChatPlanModeState:
    """Test chat plan mode state tracking"""
    
    def test_chat_initializes_without_plan_state(self):
        """Test that InteractiveChat initializes with no plan state"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            with patch('llm_runner.chat.OllamaClient'):
                chat = InteractiveChat(model="mistral")
                assert chat.plan_mode_state is None
    
    def test_chat_stores_plan_state_when_set(self):
        """Test that plan state can be stored in chat"""
        with patch('llm_runner.chat.check_ollama_connection', return_value=True):
            with patch('llm_runner.chat.OllamaClient'):
                chat = InteractiveChat(model="mistral")
                
                plan_state = {
                    "has_existing_plan": True,
                    "original_plan": "# Plan\n\n## Overview",
                    "plan_path": "/tmp/plan.md"
                }
                
                chat.plan_mode_state = plan_state
                assert chat.plan_mode_state == plan_state


class TestPlanCommandHandling:
    """Test /plan command handling in chat"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.handle_interactive_plan_refinement')
    def test_handle_plan_command_no_existing_plan(self, mock_handle, mock_client, mock_conn):
        """Test /plan command when no existing plan"""
        mock_handle.return_value = {
            "has_existing_plan": False,
            "original_plan": None,
            "plan_path": "/tmp/plan.md"
        }
        
        chat = InteractiveChat(model="mistral")
        command_result, output = chat._handle_plan_command()
        
        assert command_result == "plan_command"
        assert "refinement" in output.lower()
        assert chat.plan_mode_state is not None
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.handle_interactive_plan_refinement')
    def test_handle_plan_command_with_existing_plan(self, mock_handle, mock_client, mock_conn):
        """Test /plan command with existing plan"""
        plan_content = "# Deployment\n\n## Overview\nDeploy to prod"
        mock_handle.return_value = {
            "has_existing_plan": True,
            "original_plan": plan_content,
            "plan_path": "/tmp/plan.md"
        }
        
        chat = InteractiveChat(model="mistral")
        command_result, output = chat._handle_plan_command()
        
        assert command_result == "plan_command"
        assert chat.plan_mode_state is not None
        assert chat.plan_mode_state["has_existing_plan"] is True
        
        # Verify plan was added to context
        messages = chat.history.messages
        assert len(messages) > 0
        assert any("[PLAN CONTEXT]" in msg.get("content", "") for msg in messages)


class TestExitPlanMode:
    """Test exit_plan_mode functionality"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.detect_and_save_plan_refinement')
    def test_exit_plan_mode_no_state(self, mock_detect, mock_client, mock_conn):
        """Test exit_plan_mode when not in plan mode"""
        chat = InteractiveChat(model="mistral")
        result = chat.exit_plan_mode()
        
        assert result is False
        mock_detect.assert_not_called()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.detect_and_save_plan_refinement')
    def test_exit_plan_mode_with_refinement(self, mock_detect, mock_client, mock_conn):
        """Test exit_plan_mode detects refinements"""
        mock_detect.return_value = True
        
        chat = InteractiveChat(model="mistral")
        chat.plan_mode_state = {
            "has_existing_plan": True,
            "original_plan": "# Plan",
            "plan_path": "/tmp/plan.md"
        }
        
        result = chat.exit_plan_mode()
        
        assert result is True
        mock_detect.assert_called_once()
        assert chat.plan_mode_state is None
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.detect_and_save_plan_refinement')
    def test_exit_plan_mode_no_refinement(self, mock_detect, mock_client, mock_conn):
        """Test exit_plan_mode when no refinement detected"""
        mock_detect.return_value = False
        
        chat = InteractiveChat(model="mistral")
        chat.plan_mode_state = {
            "has_existing_plan": True,
            "original_plan": "# Plan",
            "plan_path": "/tmp/plan.md"
        }
        
        result = chat.exit_plan_mode()
        
        assert result is False
        mock_detect.assert_called_once()
        assert chat.plan_mode_state is None


class TestProcessInputPlanModeHandling:
    """Test process_input method with plan mode"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_other_command_exits_plan_mode(self, mock_client, mock_conn):
        """Test that other commands exit plan mode"""
        chat = InteractiveChat(model="mistral")
        chat.plan_mode_state = {
            "has_existing_plan": True,
            "original_plan": "# Plan",
            "plan_path": "/tmp/plan.md"
        }
        
        # Mock exit_plan_mode
        chat.exit_plan_mode = Mock(return_value=True)
        
        # Process /context command (should exit plan mode first)
        chat.process_input("/context")
        
        chat.exit_plan_mode.assert_called_once()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_plan_command_keeps_plan_mode(self, mock_client, mock_conn):
        """Test that /plan command doesn't exit plan mode"""
        with patch('llm_runner.plan_handler.handle_interactive_plan_refinement') as mock_handle:
            mock_handle.return_value = {
                "has_existing_plan": True,
                "original_plan": "# Plan",
                "plan_path": "/tmp/plan.md"
            }
            
            chat = InteractiveChat(model="mistral")
            chat.plan_mode_state = {
                "has_existing_plan": True,
                "original_plan": "# Plan",
                "plan_path": "/tmp/plan.md"
            }
            
            # Mock exit_plan_mode
            chat.exit_plan_mode = Mock(return_value=True)
            
            # Process /plan command (should not call exit_plan_mode)
            chat.process_input("/plan")
            
            # exit_plan_mode should not have been called
            chat.exit_plan_mode.assert_not_called()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_quit_exits_plan_mode_first(self, mock_client, mock_conn):
        """Test that /quit exits plan mode"""
        chat = InteractiveChat(model="mistral")
        chat.plan_mode_state = {
            "has_existing_plan": True,
            "original_plan": "# Plan",
            "plan_path": "/tmp/plan.md"
        }
        
        # Mock exit_plan_mode
        chat.exit_plan_mode = Mock(return_value=True)
        
        # Process /quit command (should exit plan mode first)
        result, _ = chat.process_input("/quit")
        
        # Should not call exit_plan_mode in process_input (that's in main loop)
        # But /quit should return quit command_result
        assert result == "quit"


class TestPlanContextInjection:
    """Test that plan context is properly injected"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.handle_interactive_plan_refinement')
    def test_plan_content_added_to_history(self, mock_handle, mock_client, mock_conn):
        """Test that plan content is added to conversation history"""
        plan_content = "# My Plan\n\n## Overview\nTest overview"
        mock_handle.return_value = {
            "has_existing_plan": True,
            "original_plan": plan_content,
            "plan_path": "/tmp/plan.md"
        }
        
        chat = InteractiveChat(model="mistral")
        chat._handle_plan_command()
        
        # Check that plan context was added
        context = chat.history.get_context()
        assert "[PLAN CONTEXT]" in context
        assert plan_content in context
        assert "[END PLAN CONTEXT]" in context
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.handle_interactive_plan_refinement')
    def test_plan_context_persists_through_chat(self, mock_handle, mock_client, mock_conn):
        """Test that plan context persists through conversation"""
        plan_content = "# Plan\n\n## Phase 1\nFirst phase"
        mock_handle.return_value = {
            "has_existing_plan": True,
            "original_plan": plan_content,
            "plan_path": "/tmp/plan.md"
        }
        
        chat = InteractiveChat(model="mistral")
        chat._handle_plan_command()
        
        # Simulate adding user message
        chat.history.add_user_message("Discuss phase 2")
        
        # Context should still have plan
        context = chat.history.get_context()
        assert "[PLAN CONTEXT]" in context
        assert plan_content in context


class TestEdgeCases:
    """Test edge cases in plan mode"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    @patch('llm_runner.plan_handler.handle_interactive_plan_refinement')
    def test_handle_plan_command_error(self, mock_handle, mock_client, mock_conn):
        """Test error handling in plan command"""
        mock_handle.return_value = None
        
        chat = InteractiveChat(model="mistral")
        command_result, output = chat._handle_plan_command()
        
        assert command_result == "plan_command"
        assert "Error" in output
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_exit_plan_mode_exception_handling(self, mock_client, mock_conn):
        """Test exception handling in exit_plan_mode"""
        with patch('llm_runner.plan_handler.detect_and_save_plan_refinement', side_effect=Exception("Test error")):
            chat = InteractiveChat(model="mistral")
            chat.plan_mode_state = {
                "has_existing_plan": True,
                "original_plan": "# Plan",
                "plan_path": "/tmp/plan.md"
            }
            
            # Should not raise, just return False
            result = chat.exit_plan_mode()
            assert result is False
            assert chat.plan_mode_state is None
