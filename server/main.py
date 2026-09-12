"""
guardian-license: FastAPI Licensing & Session Server.

Exposes REST endpoints to generate cryptographically signed software licenses
and manage real-time short-lived sessions with heartbeat renewal.
"""

from datetime import datetime, timedelta, timezone
import uuid
from fastapi import FastAPI, HTTPException, status

from .models import (
    LicenseIssueRequest,
    LicensePayload,
    SignedLicenseResponse,
    SessionStartRequest,
    SessionHeartbeatRequest,
    SessionResponse
)
from .crypto import (
    generate_keypair,
    export_public_key_b64,
    sign_license_payload
)
from .sessions import SESSION_STORE

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


# --- Real-Time Session Endpoints (Step 3) ---

@app.post(
    "/sessions/start",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"]
)
def start_session(request: SessionStartRequest):
    """
    Initializes a short-lived operational session for a validated license and device.
    """
    if not request.license_id.strip() or not request.device_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="license_id and device_id are required"
        )

    record, token = SESSION_STORE.create_session(
        license_id=request.license_id,
        device_id=request.device_id,
        ttl_seconds=request.ttl_seconds,
        server_private_key=SERVER_PRIVATE_KEY
    )

    return SessionResponse(
        session_id=record.session_id,
        session_token=token,
        expires_at=record.expires_at.isoformat(),
        is_active=True,
        message="Session started successfully"
    )


@app.post(
    "/sessions/heartbeat",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Sessions"]
)
def heartbeat(request: SessionHeartbeatRequest):
    """
    Refreshes an active session token. Fails if the session has already expired.
    """
    success, record, refreshed_token, message = SESSION_STORE.process_heartbeat(
        session_id=request.session_id,
        session_token=request.session_token,
        extend_seconds=request.extend_seconds,
        server_private_key=SERVER_PRIVATE_KEY,
        server_public_key_b64=SERVER_PUBLIC_KEY_B64
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    return SessionResponse(
        session_id=record.session_id,
        session_token=refreshed_token,
        expires_at=record.expires_at.isoformat(),
        is_active=True,
        message=message
    )
