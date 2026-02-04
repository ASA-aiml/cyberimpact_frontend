"""
================================================================================
SESSION MANAGER - UUID-Based Virtual Environment Isolation
================================================================================

DESCRIPTION:
    Manages isolated virtual environments for each user session. Each session
    gets a unique UUID and a dedicated Python virtual environment where 
    repositories are cloned and scanned in complete isolation.

CORE FUNCTIONS:
    1. Session Creation: Generates UUID and creates Python venv
    2. Session Tracking: Maintains active sessions with metadata
    3. Automatic Cleanup: Removes venv when session expires or client disconnects
    4. Background Cleanup: Periodically removes orphaned sessions

SECURITY:
    - Each session is isolated with its own venv
    - Session ownership validated against Firebase UID
    - Automatic cleanup prevents resource exhaustion
    - No cross-session data access possible

AUTHOR: ABhiram PS
DATE: 2026-02-04
================================================================================
"""

import os
import shutil
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages isolated virtual environments for user sessions"""
    
    def __init__(self, base_dir: str = "/tmp/cyberimpact", timeout_minutes: int = 60):
        """
        Initialize the session manager.
        
        Args:
            base_dir: Base directory for all sessions (default: /tmp/cyberimpact)
            timeout_minutes: Session timeout in minutes (default: 60)
        """
        self.base_dir = Path(base_dir)
        self.timeout_minutes = timeout_minutes
        self.sessions: Dict[str, dict] = {}
        self.lock = threading.Lock()
        
        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Start background cleanup thread
        self.cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"SessionManager initialized with base_dir={base_dir}, timeout={timeout_minutes}min")
    
    def create_session(self, user_id: str) -> dict:
        """
        Create a new session with isolated virtual environment.
        
        Args:
            user_id: Firebase UID of the user
            
        Returns:
            dict: Session information including session_id, paths, and metadata
        """
        session_id = str(uuid.uuid4())
        
        # Create session directory structure
        session_dir = self.base_dir / session_id
        venv_dir = session_dir / "venv"
        repos_dir = session_dir / "repos"
        
        try:
            # Create directories
            session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            repos_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Create Python virtual environment
            logger.info(f"Creating virtual environment for session {session_id}")
            subprocess.run(
                ["python3", "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Store session metadata
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now(),
                "last_access": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=self.timeout_minutes),
                "session_dir": str(session_dir),
                "venv_dir": str(venv_dir),
                "repos_dir": str(repos_dir),
                "venv_python": str(venv_dir / "bin" / "python"),
                "venv_pip": str(venv_dir / "bin" / "pip")
            }
            
            with self.lock:
                self.sessions[session_id] = session_data
            
            logger.info(f"Session {session_id} created for user {user_id}")
            return session_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create venv for session {session_id}: {e.stderr}")
            # Cleanup on failure
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to create virtual environment: {e.stderr}")
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {str(e)}")
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
            raise
    
    def get_session(self, session_id: str, user_id: str) -> Optional[dict]:
        """
        Get session data if it exists and belongs to the user.
        
        Args:
            session_id: UUID of the session
            user_id: Firebase UID to verify ownership
            
        Returns:
            dict: Session data or None if not found/unauthorized
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return None
            
            # Verify ownership
            if session["user_id"] != user_id:
                logger.warning(f"User {user_id} attempted to access session {session_id} owned by {session['user_id']}")
                return None
            
            # Check if expired
            if datetime.now() > session["expires_at"]:
                logger.info(f"Session {session_id} has expired")
                self._cleanup_session(session_id)
                return None
            
            # Update last access time
            session["last_access"] = datetime.now()
            
            return session
    
    def update_heartbeat(self, session_id: str, user_id: str) -> bool:
        """
        Update session heartbeat to keep it alive.
        
        Args:
            session_id: UUID of the session
            user_id: Firebase UID to verify ownership
            
        Returns:
            bool: True if updated, False if session not found/unauthorized
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session or session["user_id"] != user_id:
                return False
            
            # Extend expiration time
            session["last_access"] = datetime.now()
            session["expires_at"] = datetime.now() + timedelta(minutes=self.timeout_minutes)
            
            logger.debug(f"Heartbeat updated for session {session_id}")
            return True
    
    def cleanup_session(self, session_id: str, user_id: str) -> bool:
        """
        Manually cleanup a session (user-initiated).
        
        Args:
            session_id: UUID of the session
            user_id: Firebase UID to verify ownership
            
        Returns:
            bool: True if cleaned up, False if not found/unauthorized
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session or session["user_id"] != user_id:
                return False
            
            return self._cleanup_session(session_id)
    
    def _cleanup_session(self, session_id: str) -> bool:
        """
        Internal cleanup method (assumes lock is held or not needed).
        
        Args:
            session_id: UUID of the session
            
        Returns:
            bool: True if cleaned up successfully
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session_dir = Path(session["session_dir"])
        
        try:
            # Remove entire session directory (venv + repos)
            if session_dir.exists():
                logger.info(f"Removing session directory: {session_dir}")
                shutil.rmtree(session_dir, ignore_errors=True)
            
            # Remove from active sessions
            del self.sessions[session_id]
            
            logger.info(f"Session {session_id} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {str(e)}")
            return False
    
    def _background_cleanup(self):
        """Background thread that periodically cleans up expired sessions"""
        logger.info("Background cleanup thread started")
        
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                
                with self.lock:
                    expired_sessions = [
                        sid for sid, session in self.sessions.items()
                        if datetime.now() > session["expires_at"]
                    ]
                
                if expired_sessions:
                    logger.info(f"Cleaning up {len(expired_sessions)} expired sessions")
                    for session_id in expired_sessions:
                        with self.lock:
                            self._cleanup_session(session_id)
                
            except Exception as e:
                logger.error(f"Error in background cleanup: {str(e)}")
    
    def get_all_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: Firebase UID
            
        Returns:
            list: List of session data for the user
        """
        with self.lock:
            return [
                {
                    "session_id": sid,
                    "created_at": session["created_at"].isoformat(),
                    "last_access": session["last_access"].isoformat(),
                    "expires_at": session["expires_at"].isoformat()
                }
                for sid, session in self.sessions.items()
                if session["user_id"] == user_id
            ]


# Global session manager instance
session_manager = SessionManager()
