"""
guardian-license: In-memory Update Catalog & OTA Release Manager.
"""
from datetime import datetime, timezone
import hashlib
from .crypto import sign_payload

# We calculate the actual hash of a simulated correct file so the demo passes Case A
SIMULATED_VALID_PACKAGE = b"This is the binary content of the v1.1.0 software update."
VALID_PACKAGE_HASH = hashlib.sha256(SIMULATED_VALID_PACKAGE).hexdigest()

# Simulated catalog of software releases
RELEASE_CATALOG = [
    {
        "version": "1.0.0",
        "download_url": "https://cdn.guardian-demo.local/releases/v1.0.0/app-windows-amd64.zip",
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "notes": "Initial release.",
        "published_at": "2026-09-01T10:00:00+00:00"
    },
    {
        "version": "1.1.0",
        "download_url": "https://cdn.guardian-demo.local/releases/v1.1.0/app-windows-amd64.zip",
        "checksum_sha256": VALID_PACKAGE_HASH,
        "notes": "Security patches, performance improvements, and OTA support.",
        "published_at": datetime.now(timezone.utc).isoformat()
    }
]

def get_latest_release_signed(server_private_key, server_public_key_b64: str):
    """Returns the latest release payload and its cryptographic signature."""
    latest = RELEASE_CATALOG[-1]
    signature = sign_payload(server_private_key, latest)
    return latest, signature, server_public_key_b64

