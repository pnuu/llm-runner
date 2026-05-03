"""Session preservation and restoration module"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from llm_runner.session_manager import SessionManager


class SessionPreserver:
    """Manages session preservation and restoration for session continuity"""
    
    def __init__(self, session_dir: Optional[str] = None, manager: Optional[SessionManager] = None):
        """Initialize session preserver
        
        Args:
            session_dir: Directory for session storage
            manager: SessionManager instance (creates new if not provided)
        """
        if manager is None:
            self.manager = SessionManager(session_dir=session_dir)
        else:
            self.manager = manager
        
        self.session_dir = Path(session_dir or self.manager.session_dir)
    
    def get_last_session(self) -> Optional[Dict]:
        """Get the last active session
        
        Returns:
            Last session dict or None
        """
        sessions = self.manager.list_sessions()
        if not sessions:
            return None
        
        # Find most recent by creation time
        most_recent = max(sessions, key=lambda s: s.get('created_at', ''))
        return most_recent
    
    def restore_session(self, session_id: str) -> Optional[Dict]:
        """Restore a session by ID
        
        Args:
            session_id: Session ID to restore
            
        Returns:
            Session dict or None if not found
        """
        try:
            return self.manager.get_session(session_id)
        except (FileNotFoundError, KeyError):
            return None
    
    def preserve_current(self, session_id: str) -> None:
        """Preserve current session state
        
        Args:
            session_id: Session to preserve
        """
        session = self.manager.get_session(session_id)
        if session:
            self.manager.save_session(session_id)
    
    def list_all_sessions(self) -> List[Dict]:
        """List all available sessions
        
        Returns:
            List of session dicts with metadata
        """
        sessions = self.manager.list_sessions()
        # Sort by created_at descending (most recent first)
        return sorted(sessions, key=lambda s: s.get('created_at', ''), reverse=True)
    
    def create_new_session(self, model: str, name: Optional[str] = None) -> str:
        """Create a new session
        
        Args:
            model: LLM model to use
            name: Optional session name
            
        Returns:
            New session ID
        """
        session = self.manager.create_session(model=model)
        session_id = session['id']
        
        if name:
            self.rename_session(session_id, name)
        
        return session_id
    
    def rename_session(self, session_id: str, new_name: str) -> None:
        """Rename a session
        
        Args:
            session_id: Session to rename
            new_name: New session name
        """
        session = self.manager.get_session(session_id)
        session['name'] = new_name
        self.manager.save_session(session_id)
    
    def add_tags(self, session_id: str, tags: List[str]) -> None:
        """Add tags to a session
        
        Args:
            session_id: Session to tag
            tags: Tags to add
        """
        session = self.manager.get_session(session_id)
        if 'tags' not in session:
            session['tags'] = []
        
        # Avoid duplicates
        session['tags'] = list(set(session['tags'] + tags))
        self.manager.save_session(session_id)
    
    def remove_tags(self, session_id: str, tags: List[str]) -> None:
        """Remove tags from session
        
        Args:
            session_id: Session to untag
            tags: Tags to remove
        """
        session = self.manager.get_session(session_id)
        if 'tags' in session:
            session['tags'] = [t for t in session['tags'] if t not in tags]
            self.manager.save_session(session_id)
    
    def search_sessions(self, query: str) -> List[Dict]:
        """Search sessions by name or tags
        
        Args:
            query: Search query
            
        Returns:
            List of matching sessions
        """
        sessions = self.list_all_sessions()
        query_lower = query.lower()
        
        results = []
        for session in sessions:
            # Search in name
            if 'name' in session and query_lower in session['name'].lower():
                results.append(session)
                continue
            
            # Search in tags
            if 'tags' in session:
                for tag in session['tags']:
                    if query_lower in tag.lower():
                        results.append(session)
                        break
        
        return results
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get session summary with metadata
        
        Args:
            session_id: Session ID
            
        Returns:
            Summary dict with key info
        """
        session = self.manager.get_session(session_id)
        if not session:
            return None
        
        return {
            'id': session['id'],
            'model': session['model'],
            'name': session.get('name', 'Untitled'),
            'created_at': session['created_at'],
            'message_count': len(session.get('messages', [])),
            'token_count': session.get('token_count', 0),
            'tags': session.get('tags', []),
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session
        
        Args:
            session_id: Session to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.manager.delete_session(session_id)
            return True
        except FileNotFoundError:
            return False
    
    def resume_previous_session(self) -> Optional[str]:
        """Resume the previous session (auto-restore on startup)
        
        Returns:
            Session ID of resumed session, or None
        """
        last = self.get_last_session()
        if last:
            return last['id']
        return None
    
    def export_session(self, session_id: str, filepath: str) -> bool:
        """Export session to file
        
        Args:
            session_id: Session to export
            filepath: Destination file path
            
        Returns:
            True if successful
        """
        session = self.manager.get_session(session_id)
        if not session:
            return False
        
        self.manager.export_session(session_id, filepath)
        return True
    
    def import_session(self, filepath: str) -> Optional[str]:
        """Import session from file
        
        Args:
            filepath: Source file path
            
        Returns:
            Imported session ID, or None
        """
        try:
            return self.manager.import_session(filepath)
        except Exception:
            return None
