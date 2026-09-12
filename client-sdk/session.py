"""
guardian-license Client SDK: Session Manager and Heartbeat Lifecycle Control.

Maintains client session state, evaluates real-time token validity, and enforces
an application lockout (SessionExpiredError) when heartbeats fail or expire.
"""

from datetime import datetime, timezone
from typing import Callable, Optional, Tuple


class SessionExpiredError(Exception):
    """Raised when an operation is attempted with an expired or unrenewed session."""
    pass


class SessionManager:
    """
    Client-side session supervisor.
    
    Tracks the active short-lived token and its expiration deadline.
    If the session expires before being renewed via heartbeat, the manager
    enters a locked state, blocking further application operations.
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.session_id: Optional[str] = None
        self.session_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.is_locked: bool = True

    def initialize_session(self, session_id: str, session_token: str, expires_at_iso: str) -> None:
        """Initializes client state with a newly acquired session from the server."""
        self.session_id = session_id
        self.session_token = session_token
        self.expires_at = datetime.fromisoformat(expires_at_iso)
        self.is_locked = False

    def is_session_valid(self) -> bool:
        """
        Evaluates whether the session is active and unexpired against current UTC time.
        If expired, automatically locks the session.
        """
        if self.is_locked or not self.expires_at:
            return False

        now = datetime.now(timezone.utc)
        if now >= self.expires_at:
            self.is_locked = True
            return False

        return True

    def seconds_remaining(self) -> float:
        """Returns the number of seconds remaining before the session expires."""
        if not self.expires_at:
            return 0.0
        diff = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, diff)

    def assert_active(self) -> None:
        """
        Enforces execution protection. Raises SessionExpiredError if the session
        has expired or is locked, acting as an application lock overlay.
        """
        if not self.is_session_valid():
            raise SessionExpiredError(
                "[LOCKOUT] Application execution locked: active session has expired. "
                "Periodic heartbeat was interrupted or rejected by server."
            )

    def apply_heartbeat_renewal(self, new_token: str, new_expires_at_iso: str) -> None:
        """Updates session expiration upon receiving a successful heartbeat response."""
        self.session_token = new_token
        self.expires_at = datetime.fromisoformat(new_expires_at_iso)
        self.is_locked = False

    def simulate_heartbeat_cycle(
        self,
        heartbeat_fn: Callable[[str, str], Tuple[bool, Optional[str], Optional[str], str]]
    ) -> bool:
        """
        Simulates executing a heartbeat request via a provided callback function.
        Returns True if extended successfully, or False if rejected.
        """
        if not self.session_id or not self.session_token:
            return False

        success, _, new_token, new_expiry = heartbeat_fn(self.session_id, self.session_token)
        if success and new_token and new_expiry:
            self.apply_heartbeat_renewal(new_token, new_expiry)
            return True
        else:
            self.is_locked = True
            return False
