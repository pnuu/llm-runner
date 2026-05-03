"""Session management and storage module"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from llm_runner.context_manager import estimate_tokens


class SessionManager:
    """Manages session storage and persistence"""
    
    def __init__(self, session_dir: Optional[str] = None, auto_save: bool = False):
        """Initialize session manager
        
        Args:
            session_dir: Directory to store sessions (default: ~/.llm_runner/sessions)
            auto_save: Whether to auto-save sessions after modifications
        """
        if session_dir is None:
            session_dir = str(Path.home() / ".llm_runner" / "sessions")
        
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save
        self.sessions = {}  # In-memory cache
    
    def create_session(self, model: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session
        
        Args:
            model: LLM model name
            context: Optional initial context
            
        Returns:
            Session dictionary
        """
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "session_id": session_id,
            "model": model,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "token_count": 0,
            "context": context
        }
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session from memory or disk
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dictionary
            
        Raises:
            KeyError: If session not found
        """
        if session_id not in self.sessions:
            # Try to load from disk
            self.load_session(session_id)
        
        if session_id not in self.sessions:
            raise KeyError(f"Session not found: {session_id}")
        
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add message to session
        
        Args:
            session_id: Session ID
            role: Message role ("user" or "assistant")
            content: Message content
        """
        session = self.get_session(session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(message)
        
        # Update token count
        session["token_count"] = self._calculate_token_count(session)
        
        # Auto-save if enabled
        if self.auto_save:
            self.save_session(session_id)
    
    def save_session(self, session_id: str) -> None:
        """Save session to disk
        
        Args:
            session_id: Session ID
        """
        session = self.get_session(session_id)
        session_file = self.session_dir / f"{session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from disk
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dictionary or None if not found
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file) as f:
            session = json.load(f)
        
        self.sessions[session_id] = session
        return session
    
    def delete_session(self, session_id: str) -> None:
        """Delete session from memory and disk
        
        Args:
            session_id: Session ID
        """
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Remove from disk
        session_file = self.session_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions from memory and disk
        
        Returns:
            List of session dictionaries
        """
        sessions = {}
        
        # Load from disk first
        if self.session_dir.exists():
            for session_file in self.session_dir.glob("*.json"):
                with open(session_file) as f:
                    session = json.load(f)
                    sid = session.get('id') or session.get('session_id')
                    sessions[sid] = session
        
        # Overlay memory cache
        for sid, session in self.sessions.items():
            sessions[sid] = session
        
        return list(sessions.values())
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages from session
        
        Args:
            session_id: Session ID
        """
        session = self.get_session(session_id)
        session["messages"] = []
        session["token_count"] = 0
        
        if self.auto_save:
            self.save_session(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session
        
        Args:
            session_id: Session ID
            
        Returns:
            Summary dictionary
        """
        session = self.get_session(session_id)
        
        return {
            "session_id": session_id,
            "model": session["model"],
            "created_at": session["created_at"],
            "message_count": len(session["messages"]),
            "token_count": session["token_count"],
            "context": session.get("context")
        }
    
    def _calculate_token_count(self, session: Dict[str, Any]) -> int:
        """Calculate total token count for session
        
        Args:
            session: Session dictionary
            
        Returns:
            Estimated token count
        """
        total = 0
        for msg in session["messages"]:
            total += estimate_tokens(msg["content"])
        return total
    
    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages from session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        session = self.get_session(session_id)
        return session["messages"].copy()
    
    def export_session(self, session_id: str) -> str:
        """Export session as JSON string
        
        Args:
            session_id: Session ID
            
        Returns:
            JSON string representation
        """
        session = self.get_session(session_id)
        return json.dumps(session, indent=2)
    
    def import_session(self, session_data: str) -> str:
        """Import session from JSON string
        
        Args:
            session_data: JSON string with session data
            
        Returns:
            Session ID of imported session
        """
        data = json.loads(session_data)
        session_id = data.get("session_id", str(uuid.uuid4()))
        data["session_id"] = session_id
        
        self.sessions[session_id] = data
        self.save_session(session_id)
        
        return session_id
