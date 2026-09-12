"""
guardian-license: FastAPI Licensing Server.

Exposes REST endpoints to generate cryptographically signed software licenses.
"""

from datetime import datetime, timedelta, timezone
import uuid
from fastapi import FastAPI, HTTPException, status

from .models import LicenseIssueRequest, LicensePayload, SignedLicenseResponse
from .crypto import (
    generate_keypair,
    export_public_key_b64,
    sign_license_payload
)

app = FastAPI(
    title="GuardianLicense Server",
    description="Asymmetric Software Licensing API (Ed25519) — Demo Architecture",
    version="1.0.0"
)

# Ephemeral demo keypair initialized on server startup
# In production, keys must be loaded from HSM or secure environment secrets.
SERVER_PRIVATE_KEY, SERVER_PUBLIC_KEY = generate_keypair()
SERVER_PUBLIC_KEY_B64 = export_public_key_b64(SERVER_PUBLIC_KEY)


@app.get("/health", tags=["Status"])
def health_check():
    """Health check endpoint confirming licensing server availability."""
    return {"status": "online", "engine": "Ed25519"}


@app.get("/public-key", tags=["Crypto"])
def get_public_key():
    """Returns the server's public key in base64 format for client verification."""
    return {"public_key_b64": SERVER_PUBLIC_KEY_B64}


@app.post(
    "/licenses/issue",
    response_model=SignedLicenseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Licensing"]
)
def issue_license(request: LicenseIssueRequest):
    """
    Issues an asymmetric cryptographically signed software license
    bound to a target device identifier.
    """
    if not request.device_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id must not be empty"
        )

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=request.expires_in_days)

    payload_dict = {
        "license_id": f"LIC-{uuid.uuid4().hex[:12].upper()}",
        "product_name": request.product_name,
        "device_id": request.device_id.strip(),
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat()
    }

    # Sign canonical payload bytes using server private key
    signature = sign_license_payload(SERVER_PRIVATE_KEY, payload_dict)

    return SignedLicenseResponse(
        payload=LicensePayload(**payload_dict),
        signature=signature,
        public_key_b64=SERVER_PUBLIC_KEY_B64
    )
