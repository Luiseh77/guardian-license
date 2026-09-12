"""
guardian-license: Cryptographic engine using Ed25519 asymmetric signatures.

Provides canonical payload serialization, keypair generation,
and digital signature creation for software license bundles.
"""

import base64
import json
from typing import Any, Dict, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Generates a new Ed25519 keypair for demonstration purposes.
    
    WARNING: For production use, private keys must be stored in secure
    secret managers (e.g. AWS Secrets Manager, HashiCorp Vault) or HSMs.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def export_public_key_b64(public_key: ed25519.Ed25519PublicKey) -> str:
    """Exports an Ed25519 public key as a base64 encoded raw bytes string."""
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw_bytes).decode("utf-8")


def export_private_key_b64(private_key: ed25519.Ed25519PrivateKey) -> str:
    """Exports an Ed25519 private key as a base64 encoded raw bytes string."""
    raw_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    return base64.b64encode(raw_bytes).decode("utf-8")


def load_public_key_from_b64(pub_b64: str) -> ed25519.Ed25519PublicKey:
    """Loads an Ed25519 public key from base64 raw bytes."""
    raw_bytes = base64.b64decode(pub_b64)
    return ed25519.Ed25519PublicKey.from_public_bytes(raw_bytes)


def load_private_key_from_b64(priv_b64: str) -> ed25519.Ed25519PrivateKey:
    """Loads an Ed25519 private key from base64 raw bytes."""
    raw_bytes = base64.b64decode(priv_b64)
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)


def serialize_canonical_payload(payload: Dict[str, Any]) -> bytes:
    """
    Serializes a dictionary into canonical UTF-8 JSON bytes with sorted keys
    and compact separators, ensuring bit-for-bit determinism across platforms.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_license_payload(
    private_key: ed25519.Ed25519PrivateKey,
    payload: Dict[str, Any]
) -> str:
    """
    Signs a license payload using the server's Ed25519 private key.
    
    Returns the signature encoded in base64.
    """
    canonical_bytes = serialize_canonical_payload(payload)
    signature_bytes = private_key.sign(canonical_bytes)
    return base64.b64encode(signature_bytes).decode("utf-8")
