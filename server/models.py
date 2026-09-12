"""
guardian-license: Pydantic schemas and models for license issuance.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
