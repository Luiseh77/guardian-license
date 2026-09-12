"""
guardian-license: In-memory Session Manager & Real-Time Lifecycle Control.

Provides short-lived session tracking and heartbeat renewal to enforce
near real-time application authorization and revocation.
"""

import sys
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
import uuid

from .crypto import sign_payload

# Allow importing verifier from client-sdk
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "client-sdk"))
from verifier import verify_signature


@dataclass
class SessionRecord:
    session_id: str
    license_id: str
    device_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class SessionStore:
    """In-memory thread-safe session store for demonstration purposes."""

    def __init__(self):
        self._sessions: Dict[str, SessionRecord] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        license_id: str,
        device_id: str,
        ttl_seconds: int,
        server_private_key
    ) -> Tuple[SessionRecord, str]:
        """
        Creates a new short-lived session and returns the record and a signed session token.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        session_id = f"SES-{uuid.uuid4().hex[:12].upper()}"

        record = SessionRecord(
            session_id=session_id,
            license_id=license_id.strip(),
            device_id=device_id.strip(),
            created_at=now,
            expires_at=expires_at,
            is_active=True
        )
        
        with self._lock:
            self._sessions[session_id] = record

        # Generate a signed short-lived session token
        token_payload = {
            "session_id": session_id,
            "device_id": device_id.strip(),
            "expires_at": expires_at.isoformat(),
            "type": "short_lived_session"
        }
        token = sign_payload(server_private_key, token_payload)

        return record, token

    def process_heartbeat(
        self,
        session_id: str,
        session_token: str,
        extend_seconds: int,
        server_private_key,
        server_public_key_b64: str
    ) -> Tuple[bool, Optional[SessionRecord], Optional[str], str]:
        """
        Processes a heartbeat for an existing session.
        
        Enforces strict rules:
        - Session must exist.
        - The provided session_token must be cryptographically valid for this session.
        - Session must be currently active and NOT yet expired.
        - If expired, heartbeat is rejected (requiring a full session re-initialization).
        
        Returns:
            (success: bool, record: Optional[SessionRecord], new_token: Optional[str], message: str)
        """
        with self._lock:
            record = self._sessions.get(session_id)
            if not record or not record.is_active:
                return False, None, None, "Session not found or terminated."

            # Verify the token signature and structure
            expected_payload = {
                "session_id": session_id,
                "device_id": record.device_id,
                "expires_at": record.expires_at.isoformat(),
                "type": "short_lived_session"
            }
            
            is_valid_token = verify_signature(server_public_key_b64, expected_payload, session_token)
            if not is_valid_token:
                # Token mismatch or forged
                record.is_active = False
                return False, record, None, "Heartbeat rejected: invalid or forged session token."

            now = datetime.now(timezone.utc)
            if now > record.expires_at:
                # Mark session as expired/inactive
                record.is_active = False
                return (
                    False,
                    record,
                    None,
                    f"Heartbeat rejected: session {session_id} expired at {record.expires_at.isoformat()}. Re-authentication required."
                )

            # Extend validity
            record.expires_at = now + timedelta(seconds=extend_seconds)

            # Issue refreshed signed token with updated expiration
            token_payload = {
                "session_id": session_id,
                "device_id": record.device_id,
                "expires_at": record.expires_at.isoformat(),
                "type": "short_lived_session"
            }
            refreshed_token = sign_payload(server_private_key, token_payload)

            return True, record, refreshed_token, "Heartbeat successful: session extended."


# Global in-memory session store instance for server runtime
SESSION_STORE = SessionStore()

