"""
guardian-license: Pydantic schemas and models for license issuance and session management.
"""

from typing import Optional
from pydantic import BaseModel, Field


# --- License Issuance Schemas ---

class LicenseIssueRequest(BaseModel):
    device_id: str = Field(
        ...,
        description="Unique client device identifier bound to the license",
        example="DEV-8841BEEF-90EE41AC-7789ABCD"
    )
    expires_in_days: Optional[int] = Field(
        default=30,
        description="License validity period in days",
        ge=1,
        le=365
    )
    product_name: Optional[str] = Field(
        default="GuardianLicense Demo",
        description="Fictional product identifier"
    )


class LicensePayload(BaseModel):
    license_id: str = Field(..., description="Unique license identifier")
    product_name: str = Field(..., description="Licensed software product")
    device_id: str = Field(..., description="Target bound device identifier")
    issued_at: str = Field(..., description="ISO 8601 issuance timestamp")
    expires_at: str = Field(..., description="ISO 8601 expiration timestamp")


class SignedLicenseResponse(BaseModel):
    payload: LicensePayload
    signature: str = Field(..., description="Base64 encoded Ed25519 digital signature")
    public_key_b64: str = Field(
        ...,
        description="Server public key (included in demo for testing verification)"
    )


# --- Session Management Schemas (Step 3) ---

class SessionStartRequest(BaseModel):
    license_id: str = Field(..., description="Issued license ID")
    device_id: str = Field(..., description="Hardware identifier of the client machine")
    ttl_seconds: Optional[int] = Field(
        default=300,
        description="Session duration in seconds (short-lived, e.g. 300s in prod or 2-5s in demo)",
        ge=1,
        le=3600
    )


class SessionHeartbeatRequest(BaseModel):
    session_id: str = Field(..., description="Active session identifier")
    session_token: str = Field(..., description="Current signed short-lived session token")
    extend_seconds: Optional[int] = Field(
        default=300,
        description="Additional duration to extend the active session",
        ge=1,
        le=3600
    )


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="Active session identifier")
    session_token: str = Field(..., description="Signed short-lived session token")
    expires_at: str = Field(..., description="ISO 8601 timestamp when the session expires")
    is_active: bool = Field(default=True, description="Session status")
    message: str = Field(default="Session active", description="Status message")
