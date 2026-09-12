"""
guardian-license Client SDK: Over-The-Air (OTA) Update Verifier.

Verifies that update announcements come from the authorized server and
ensures that downloaded packages have not been tampered with or corrupted.
"""

import hashlib
from typing import Any, Dict, Tuple
from verifier import verify_signature

def verify_update_announcement(
    public_key_b64: str,
    payload: Dict[str, Any],
    signature_b64: str
) -> Tuple[bool, str]:
    """
    Verifies the authenticity and integrity of the update announcement.
    Uses the same Ed25519 signature mechanism as the licensing core.
    """
    is_valid = verify_signature(public_key_b64, payload, signature_b64)
    if not is_valid:
        return False, "Update announcement signature verification failed. Possible MitM attack."
    return True, "Update announcement is authentic."

def verify_downloaded_file(
    file_bytes: bytes,
    expected_checksum_sha256: str
) -> Tuple[bool, str]:
    """
    Calculates the SHA-256 hash of the downloaded file bytes and compares it
    to the expected checksum provided in the authenticated announcement.
    """
    calculated_hash = hashlib.sha256(file_bytes).hexdigest()
    if calculated_hash.lower() != expected_checksum_sha256.lower():
        return False, (
            f"File integrity check failed!\n"
            f"Expected:   {expected_checksum_sha256.lower()}\n"
            f"Calculated: {calculated_hash}\n"
            f"The package is corrupted or has been tampered with."
        )
    
    return True, "File integrity verified successfully. Safe to apply update."

