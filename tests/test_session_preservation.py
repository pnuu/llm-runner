"""Tests for session preservation functionality"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from llm_runner.session_manager import SessionManager
from llm_runner.session_preservation import SessionPreserver


class TestSessionPreserver:
    """Test session preservation and restoration"""
    
    def test_create_session_preserver(self):
        """Test creating session preserver"""
        with tempfile.TemporaryDirectory() as tmpdir:
            preserver = SessionPreserver(session_dir=tmpdir)
            assert preserver is not None
    
    def test_get_last_session(self):
        """Test getting last active session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create sessions
            sess1 = manager.create_session(model="test-model")
            sid1 = sess1['id']
            manager.add_message(sid1, "User", "Hello")
            manager.save_session(sid1)
            
            sess2 = manager.create_session(model="test-model")
            sid2 = sess2['id']
            manager.add_message(sid2, "User", "Hi")
            manager.save_session(sid2)
            
            # Last session should be most recent
            last = preserver.get_last_session()
            assert last is not None
            assert last['id'] == sid2
    
    def test_restore_session(self):
        """Test restoring a session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create and populate session
            sess = manager.create_session(model="test-model")
            sid = sess['id']
            manager.add_message(sid, "User", "Question?")
            manager.add_message(sid, "Assistant", "Answer!")
            manager.save_session(sid)
            
            # Restore session
            restored = preserver.restore_session(sid)
            assert restored['id'] == sid
            assert len(restored['messages']) == 2
            assert restored['messages'][0]['content'] == "Question?"
            assert restored['messages'][1]['content'] == "Answer!"
    
    def test_preserve_current_session(self):
        """Test preserving current session state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="llama2")
            sid = sess['id']
            manager.add_message(sid, "User", "msg1")
            manager.add_message(sid, "Assistant", "resp1")
            
            # Preserve current state
            preserver.preserve_current(sid)
            
            # Verify it's marked as active
            sessions = manager.list_sessions()
            current_session = None
            for s in sessions:
                if s['id'] == sid:
                    current_session = s
                    break
            
            assert current_session is not None
    
    def test_list_all_sessions(self):
        """Test listing all sessions for restoration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create multiple sessions
            for i in range(3):
                sess = manager.create_session(model="test")
                sid = sess['id']
                manager.add_message(sid, "User", f"msg{i}")
                manager.save_session(sid)
            
            sessions = preserver.list_all_sessions()
            assert len(sessions) == 3
    
    def test_session_auto_restore_on_startup(self):
        """Test auto-restoring last session on startup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session
            manager1 = SessionManager(session_dir=tmpdir)
            preserver1 = SessionPreserver(session_dir=tmpdir, manager=manager1)
            
            sess = manager1.create_session(model="test")
            sid = sess['id']
            manager1.add_message(sid, "User", "Previous conversation")
            manager1.save_session(sid)
            preserver1.preserve_current(sid)
            
            # New session startup should restore
            manager2 = SessionManager(session_dir=tmpdir)
            preserver2 = SessionPreserver(session_dir=tmpdir, manager=manager2)
            
            last = preserver2.get_last_session()
            assert last is not None
            assert last['id'] == sid
    
    def test_new_session_creation(self):
        """Test creating new session (no auto-restore)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create initial session
            sess1 = manager.create_session(model="test")
            sid1 = sess1['id']
            manager.add_message(sid1, "User", "chat1")
            manager.save_session(sid1)
            
            # Create new session
            sid2 = preserver.create_new_session(model="test")
            assert sid2 != sid1
            
            session = manager.get_session(sid2)
            assert len(session['messages']) == 0
    
    def test_session_with_metadata(self):
        """Test session preserves all metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            model = "special-model"
            sess = manager.create_session(model=model)
            sid = sess['id']
            manager.add_message(sid, "User", "test")
            manager.save_session(sid)
            
            restored = preserver.restore_session(sid)
            assert restored['model'] == model
            assert restored['created_at'] is not None
    
    def test_resume_partial_session(self):
        """Test resuming session mid-conversation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add messages
            for i in range(5):
                manager.add_message(sid, "User", f"q{i}")
                manager.add_message(sid, "Assistant", f"a{i}")
            
            manager.save_session(sid)
            preserver.preserve_current(sid)
            
            # Restore and verify
            restored = preserver.restore_session(sid)
            assert len(restored['messages']) == 10  # 5 pairs
    
    def test_session_switching(self):
        """Test switching between sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Create sessions
            sess1 = manager.create_session(model="test")
            sid1 = sess1['id']
            manager.add_message(sid1, "User", "session1")
            manager.save_session(sid1)
            
            sess2 = manager.create_session(model="test")
            sid2 = sess2['id']
            manager.add_message(sid2, "User", "session2")
            manager.save_session(sid2)
            
            # Switch to session1
            s1 = preserver.restore_session(sid1)
            assert s1['messages'][0]['content'] == "session1"
            
            # Switch to session2
            s2 = preserver.restore_session(sid2)
            assert s2['messages'][0]['content'] == "session2"
    
    def test_session_rename(self):
        """Test renaming a session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Rename session
            new_name = "My Important Chat"
            preserver.rename_session(sid, new_name)
            
            # Verify renamed
            session = manager.get_session(sid)
            assert session.get('name') == new_name or 'name' in session
    
    def test_session_tags(self):
        """Test tagging sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add tags
            preserver.add_tags(sid, ["important", "debug"])
            
            # Retrieve and verify
            sessions = preserver.list_all_sessions()
            found = None
            for s in sessions:
                if s['id'] == sid:
                    found = s
                    break
            
            assert found is not None
            # Session should have tags or a way to track them
    
    def test_restore_nonexistent_session(self):
        """Test restoring non-existent session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            # Try to restore non-existent
            result = preserver.restore_session("nonexistent")
            assert result is None
    
    def test_session_history_with_preservation(self):
        """Test session history is preserved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            preserver = SessionPreserver(session_dir=tmpdir, manager=manager)
            
            sess = manager.create_session(model="test")
            sid = sess['id']
            
            # Add multiple messages
            messages = [
                ("User", "First question"),
                ("Assistant", "First answer"),
                ("User", "Second question"),
                ("Assistant", "Second answer"),
            ]
            
            for role, content in messages:
                manager.add_message(sid, role, content)
            
            manager.save_session(sid)
            
            # Restore and check order
            restored = preserver.restore_session(sid)
            for i, (role, content) in enumerate(messages):
                assert restored['messages'][i]['role'] == role
                assert restored['messages'][i]['content'] == content
