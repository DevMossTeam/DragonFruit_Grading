# auth/session.py
import uuid
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# In-memory cache for faster access
sessions: Dict[str, dict] = {}

# Session file for persistence (survives server restarts)
SESSION_FILE = os.path.join(os.path.dirname(__file__), '../../temp/sessions.json')

def _ensure_temp_dir():
    """Create temp directory if it doesn't exist"""
    temp_dir = os.path.dirname(SESSION_FILE)
    os.makedirs(temp_dir, exist_ok=True)

def _load_sessions_from_file():
    """Load sessions from persistent storage"""
    global sessions
    _ensure_temp_dir()
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                # Convert ISO strings back to datetime
                for sid, session in data.items():
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                    session['expires_at'] = datetime.fromisoformat(session['expires_at'])
                sessions = data
                logger.info(f"✅ Loaded {len(sessions)} sessions from disk")
    except Exception as e:
        logger.error(f"❌ Error loading sessions from file: {e}")
        sessions = {}

def _save_sessions_to_file():
    """Save sessions to persistent storage"""
    _ensure_temp_dir()
    try:
        # Convert datetime to ISO strings for JSON serialization
        data = {}
        for sid, session in sessions.items():
            data[sid] = {
                "user_id": session["user_id"],
                "created_at": session["created_at"].isoformat(),
                "expires_at": session["expires_at"].isoformat()
            }
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"💾 Saved {len(sessions)} sessions to disk")
    except Exception as e:
        logger.error(f"❌ Error saving sessions to file: {e}")

# Load sessions on module import
_load_sessions_from_file()

def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sessions[session_id] = {
        "user_id": user_id,
        "created_at": now,
        "expires_at": now + timedelta(hours=1)
    }
    logger.info(f"✅ Session created: {session_id} for user: {user_id}")
    _save_sessions_to_file()  # Persist immediately
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    session = sessions.get(session_id)
    if session:
        now = datetime.now(timezone.utc)
        if session["expires_at"] > now:
            logger.info(f"✅ Session valid: {session_id}")
            return session
        # Expired session - delete it
        logger.warning(f"⏰ Session expired: {session_id}")
        del sessions[session_id]
        _save_sessions_to_file()
    else:
        logger.warning(f"❌ Session not found: {session_id}")
    return None

def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"🗑️ Session deleted: {session_id}")
        _save_sessions_to_file()
    else:
        logger.warning(f"⚠️ Session to delete not found: {session_id}")