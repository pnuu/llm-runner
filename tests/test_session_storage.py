"""Tests for session storage functionality"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from llm_runner.session_manager import SessionManager


class TestSessionManager:
    """Test session storage and management"""
    
    def test_create_session_manager(self):
        """Test creating a session manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            assert manager is not None
            assert Path(tmpdir).exists()
    
    def test_session_dir_creation(self):
        """Test that session directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(session_dir=str(session_dir))
            assert session_dir.exists()
    
    def test_create_new_session(self):
        """Test creating a new session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            
            assert session is not None
            assert "session_id" in session
            assert session["model"] == "mistral:7b"
            assert "created_at" in session
    
    def test_session_metadata(self):
        """Test session has required metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="neural-chat")
            
            assert "session_id" in session
            assert "model" in session
            assert "created_at" in session
            assert "messages" in session
            assert "token_count" in session
    
    def test_add_message_to_session(self):
        """Test adding messages to session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "Hello")
            session = manager.get_session(session_id)
            
            assert len(session["messages"]) == 1
            assert session["messages"][0]["role"] == "user"
            assert session["messages"][0]["content"] == "Hello"
    
    def test_save_session(self):
        """Test saving session to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "test")
            manager.save_session(session_id)
            
            # Verify file exists
            session_file = Path(tmpdir) / f"{session_id}.json"
            assert session_file.exists()
    
    def test_load_session(self):
        """Test loading session from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            
            # Create and save
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            manager.add_message(session_id, "user", "Question?")
            manager.add_message(session_id, "assistant", "Answer!")
            manager.save_session(session_id)
            
            # Create new manager and load
            manager2 = SessionManager(session_dir=tmpdir)
            loaded = manager2.load_session(session_id)
            
            assert loaded is not None
            assert loaded["model"] == "mistral:7b"
            assert len(loaded["messages"]) == 2
            assert loaded["messages"][0]["content"] == "Question?"
    
    def test_get_session(self):
        """Test getting session from memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            retrieved = manager.get_session(session_id)
            assert retrieved["session_id"] == session_id
    
    def test_list_sessions(self):
        """Test listing all sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            
            session1 = manager.create_session(model="mistral:7b")
            session2 = manager.create_session(model="neural-chat")
            
            sessions = manager.list_sessions()
            assert len(sessions) == 2
    
    def test_session_token_count(self):
        """Test session token count tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "x" * 100)
            session = manager.get_session(session_id)
            
            assert session["token_count"] > 0
    
    def test_delete_session(self):
        """Test deleting a session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.delete_session(session_id)
            
            with pytest.raises(KeyError):
                manager.get_session(session_id)
    
    def test_session_file_format(self):
        """Test session file is valid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "test")
            manager.save_session(session_id)
            
            # Read file directly
            session_file = Path(tmpdir) / f"{session_id}.json"
            with open(session_file) as f:
                data = json.load(f)
            
            assert data["model"] == "mistral:7b"
            assert "messages" in data
    
    def test_session_persistence_roundtrip(self):
        """Test full save and load roundtrip"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            manager1 = SessionManager(session_dir=tmpdir)
            session = manager1.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager1.add_message(session_id, "user", "Q1")
            manager1.add_message(session_id, "assistant", "A1")
            manager1.add_message(session_id, "user", "Q2")
            manager1.save_session(session_id)
            
            # Load in new manager
            manager2 = SessionManager(session_dir=tmpdir)
            loaded = manager2.load_session(session_id)
            
            assert loaded["model"] == "mistral:7b"
            assert len(loaded["messages"]) == 3
            assert loaded["messages"][0]["content"] == "Q1"
            assert loaded["messages"][1]["content"] == "A1"
            assert loaded["messages"][2]["content"] == "Q2"
    
    def test_session_context_summary(self):
        """Test getting session context summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "test 1")
            manager.add_message(session_id, "assistant", "response 1")
            
            summary = manager.get_session_summary(session_id)
            assert "model" in summary
            assert "message_count" in summary
            assert "token_count" in summary
            assert "created_at" in summary
    
    def test_auto_save_option(self):
        """Test auto-save functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir, auto_save=True)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            # Add message with auto-save
            manager.add_message(session_id, "user", "test")
            
            # Verify file exists
            session_file = Path(tmpdir) / f"{session_id}.json"
            assert session_file.exists()
    
    def test_clear_session_messages(self):
        """Test clearing session messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(session_dir=tmpdir)
            session = manager.create_session(model="mistral:7b")
            session_id = session["session_id"]
            
            manager.add_message(session_id, "user", "test1")
            manager.add_message(session_id, "assistant", "test2")
            
            manager.clear_session(session_id)
            session = manager.get_session(session_id)
            
            assert len(session["messages"]) == 0
