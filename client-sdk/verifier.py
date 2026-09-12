"""
guardian-license Client SDK: Offline License Verifier.

Verifies signed license bundles using only the server's public key.
Requires zero network connection during validation.
"""

import base64
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature


def _serialize_canonical_payload(payload: Dict[str, Any]) -> bytes:
    """Serializes a dictionary into canonical UTF-8 JSON bytes with sorted keys."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(
    public_key_b64: str,
    payload: Dict[str, Any],
    signature_b64: str
) -> bool:
    """
    Verifies that the given payload was signed by the holder of the private key
    corresponding to public_key_b64.
    """
    try:
        raw_pub_bytes = base64.b64decode(public_key_b64)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(raw_pub_bytes)
        signature_bytes = base64.b64decode(signature_b64)
        canonical_bytes = _serialize_canonical_payload(payload)

        public_key.verify(signature_bytes, canonical_bytes)
        return True
    except (InvalidSignature, ValueError, KeyError):
        return False


def validate_license(
    public_key_b64: str,
    license_bundle: Dict[str, Any],
    expected_device_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates a complete license bundle containing 'payload' and 'signature'.
    
    Checks:
    1. Bundle structure integrity.
    2. Asymmetric cryptographic signature authenticity.
    3. Expiration timestamp against current UTC time.
    4. Hardware binding match (if expected_device_id is provided).

    Returns:
        (is_valid: bool, status_message: str)
    """
    payload = license_bundle.get("payload")
    signature_b64 = license_bundle.get("signature")

    if not payload or not signature_b64:
        return False, "Malformed license bundle: missing payload or signature."

    # 1. Verify digital signature
    if not verify_signature(public_key_b64, payload, signature_b64):
        return False, "Signature verification failed: license bundle is forged or tampered."

    # 2. Check expiration
    expires_at_str = payload.get("expires_at")
    if not expires_at_str:
        return False, "License payload missing expiration timestamp."

    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now(timezone.utc)
        if now > expires_at:
            return False, f"License expired on {expires_at_str}."
    except ValueError:
        return False, "Invalid expiration date format in license payload."

    # 3. Check hardware binding (if specified)
    if expected_device_id is not None:
        licensed_device = payload.get("device_id")
        if licensed_device != expected_device_id:
            return False, (
                f"Device mismatch: license bound to '{licensed_device}', "
                f"current machine is '{expected_device_id}'."
            )

    return True, "License is authentic, valid, and bound to this device."

