"""Integration tests for Phase 5 session enhancement features"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from llm_runner.session_manager import SessionManager
from llm_runner.session_preservation import SessionPreserver
from llm_runner.history_manager import HistoryManager
from llm_runner.history_navigation import CommandLineEditor
from llm_runner.config_wizard import ConfigWizard
from llm_runner.context_manager import ContextManager


class TestPhase5Integration:
    """Test integration of Phase 5 session enhancement features"""
    
    def test_session_with_context_awareness(self):
        """Test session persistence with context tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from llm_runner.context_manager import estimate_tokens
            
            manager = SessionManager(session_dir=tmpdir)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add messages and track context
            manager.add_message(sid, "User", "Hello")
            manager.add_message(sid, "Assistant", "Hi there!")
            
            # Update token count
            session = manager.get_session(sid)
            token_count = estimate_tokens(str(session['messages']))
            session['token_count'] = token_count
            manager.save_session(sid)
            
            # Verify persistence
            restored = manager.get_session(sid)
            assert restored['token_count'] > 0
    
    def test_session_preservation_with_history(self):
        """Test session preservation integrated with command history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            history = HistoryManager(history_file=f"{tmpdir}/history")
            
            # Create session with commands
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add to session and history
            manager.add_message(sid, "User", "first query")
            history.add("chat query 1")
            
            manager.save_session(sid)
            
            # Verify both persist
            restored = preserver.restore_session(sid)
            assert len(restored['messages']) == 1
            assert history.count() == 1
    
    def test_config_affects_session_creation(self):
        """Test that config wizard settings apply to new sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_wizard = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            config_wizard.set_model("custom-model")
            config_wizard.set_temperature(0.9)
            config_wizard.save()
            
            # Create session with configured model
            manager = SessionManager(session_dir=tmpdir)
            sess = manager.create_session(model=config_wizard.get_config()['model'])
            
            assert sess['model'] == "custom-model"
    
    def test_command_editor_with_session_history(self):
        """Test command line editor with session command history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/cmd_history")
            manager = SessionManager(session_dir=tmpdir)
            
            # Add session commands to history
            editor.add_to_history("/list-sessions")
            editor.add_to_history("/clear-history")
            
            # Navigate history - should start at last item
            editor.start_navigation()
            assert editor.current() == "/clear-history"  # Most recent
            
            # Move up to see previous
            editor.move_up()
            assert editor.current() == "/list-sessions"
    
    def test_full_session_workflow(self):
        """Test complete workflow: create, populate, save, restore session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Setup
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            history = HistoryManager(history_file=f"{tmpdir}/history")
            config = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # 2. Create session with configured model
            config.set_model("test-model")
            sess = manager.create_session(model=config.get_config()['model'])
            sid = sess['id']
            
            # 3. Add messages and track in history
            manager.add_message(sid, "User", "What is Python?")
            manager.add_message(sid, "Assistant", "Python is a programming language")
            history.add("describe python")
            
            # 4. Save session
            manager.save_session(sid)
            preserver.preserve_current(sid)
            
            # 5. Restore and verify
            restored = preserver.restore_session(sid)
            assert restored['model'] == "test-model"
            assert len(restored['messages']) == 2
            assert history.count() == 1
            
            # 6. Resume - should get last session
            last = preserver.resume_previous_session()
            assert last == sid
    
    def test_session_search_with_tags(self):
        """Test searching sessions by tags"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create and tag sessions
            s1 = manager.create_session(model="test")
            sid1 = s1['id']
            preserver.add_tags(sid1, ["important", "work"])
            manager.save_session(sid1)
            
            s2 = manager.create_session(model="test")
            sid2 = s2['id']
            preserver.add_tags(sid2, ["debug", "testing"])
            manager.save_session(sid2)
            
            # Search
            work_sessions = preserver.search_sessions("work")
            assert len(work_sessions) == 1
            assert work_sessions[0]['id'] == sid1
    
    def test_context_and_session_compaction(self):
        """Test context compaction within session storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            ctx_mgr = ContextManager(max_tokens=100)  # Very small
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add many messages to trigger compaction
            for i in range(20):
                manager.add_message(sid, "User", f"msg{i}")
                manager.add_message(sid, "Assistant", f"response{i}")
            
            manager.save_session(sid)
            
            # Verify messages were saved
            session = manager.get_session(sid)
            assert len(session['messages']) == 40
    
    def test_export_and_import_session(self):
        """Test exporting and importing sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = SessionManager(session_dir=tmpdir)
            
            sess = manager1.create_session(model="test")
            sid = sess['id']
            manager1.add_message(sid, "User", "test data")
            manager1.save_session(sid)
            
            # Export to JSON string
            json_str = manager1.export_session(sid)
            
            assert json_str is not None
            assert "test data" in json_str
            
            # Import from JSON string
            manager2 = SessionManager(session_dir=f"{tmpdir}/imported")
            imported_id = manager2.import_session(json_str)
            
            # Verify content
            imported = manager2.get_session(imported_id)
            assert len(imported['messages']) == 1
            assert imported['messages'][0]['content'] == "test data"
    
    def test_history_navigation_with_session_commands(self):
        """Test navigating through session management commands"""
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CommandLineEditor(history_file=f"{tmpdir}/history")
            
            # Simulate user typing session commands
            commands = [
                "/list-sessions",
                "/save-session",
                "/load-session abc123",
                "/delete-session",
            ]
            
            for cmd in commands:
                editor.add_to_history(cmd)
            
            # Navigate backward to find a command
            editor.start_navigation()
            assert editor.current() == "/delete-session"
            
            # Search for load command
            results = editor.search("/load")
            assert len(results) == 1
            assert "/load-session" in results[0]
    
    def test_multiple_sessions_with_different_configs(self):
        """Test creating sessions with different configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            config = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            
            # Session 1 with model A
            config.set_model("model-a")
            s1 = manager.create_session(model="model-a")
            sid1 = s1['id']
            
            # Session 2 with model B
            s2 = manager.create_session(model="model-b")
            sid2 = s2['id']
            
            # Verify different configs
            sess1 = manager.get_session(sid1)
            sess2 = manager.get_session(sid2)
            
            assert sess1['model'] == "model-a"
            assert sess2['model'] == "model-b"
    
    def test_session_list_ordering(self):
        """Test that session list is ordered by creation time"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sids = []
            for i in range(3):
                sess = manager.create_session(model="test")
                sid = sess['id']
                sids.append(sid)
                manager.add_message(sid, "User", f"session{i}")
                manager.save_session(sid)
            
            # List should show most recent first
            all_sessions = preserver.list_all_sessions()
            assert all_sessions[0]['id'] == sids[-1]  # Last created first
    
    def test_config_persistence_affects_new_sessions(self):
        """Test that config persists and affects new sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Session 1: Set config
            config1 = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            config1.set_model("persistent-model")
            config1.set_temperature(0.8)
            config1.save()
            
            # Session 2: Load config
            config2 = ConfigWizard(config_file=f"{tmpdir}/config.yaml")
            cfg = config2.get_config()
            
            assert cfg['model'] == "persistent-model"
            assert cfg['temperature'] == 0.8
    
    def test_empty_session_operations(self):
        """Test operations on empty sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            manager.save_session(sid)
            
            # Empty session should still be retrievable
            restored = preserver.restore_session(sid)
            assert len(restored['messages']) == 0
            assert restored['token_count'] == 0
    
    def test_session_name_and_tags_integration(self):
        """Test naming and tagging sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Name and tag
            preserver.rename_session(sid, "My Chat")
            preserver.add_tags(sid, ["personal", "debug"])
            manager.save_session(sid)
            
            # Verify
            summary = preserver.get_session_summary(sid)
            assert summary['name'] == "My Chat"
            assert "personal" in summary['tags']
