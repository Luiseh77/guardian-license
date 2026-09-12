"""
guardian-license: End-to-End Verification Demo.

Demonstrates:
1. Server keypair generation and license issuance.
2. Client-side offline verification.
3. Tamper detection (altering expiration date or device_id invalidates signature).
"""

from datetime import datetime, timedelta, timezone
import json
import sys
import os

# Ensure clean UTF-8 console output on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add paths to allow importing from server and client-sdk
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "client-sdk"))

from server.crypto import generate_keypair, export_public_key_b64, sign_license_payload
from verifier import validate_license


def run_demo():
    print("================================================================")
    print("[*] GUARDIAN LICENSE - END-TO-END DEMO")
    print("================================================================")

    # 1. Server generates its asymmetric keypair
    server_private_key, server_public_key = generate_keypair()
    public_key_b64 = export_public_key_b64(server_public_key)
    print(f"\n[1] Clave publica del servidor (integrada en cliente):")
    print(f"    {public_key_b64[:32]}... (Longitud: {len(public_key_b64)} chars)")

    # 2. Server issues a license for a specific fictional client device
    device_id = "DEV-NODE-8841-BEEF"
    now = datetime.now(timezone.utc)
    payload = {
        "license_id": "LIC-DEMO-00123",
        "product_name": "GuardianLicense Demo",
        "device_id": device_id,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat()
    }

    # 3. Server signs the payload
    signature = sign_license_payload(server_private_key, payload)
    license_bundle = {
        "payload": payload,
        "signature": signature
    }
    print("\n[2] Licencia emitida y firmada por el servidor:")
    print(json.dumps(license_bundle, indent=2))

    # 4. Client validates the authentic license (Valid Case)
    print("\n[3] Verificacion en cliente (CASO EXITOSO):")
    is_valid, message = validate_license(
        public_key_b64=public_key_b64,
        license_bundle=license_bundle,
        expected_device_id=device_id
    )
    print(f"    Resultado: {'[PASS] VALIDA' if is_valid else '[FAIL] INVALIDA'}")
    print(f"    Detalle:   {message}")
    assert is_valid is True

    # 5. Tamper Test: Malicious user alters expiration date
    print("\n[4] Prueba de Falsificacion (CASO ALTERACION DE EXPIRACION):")
    tampered_bundle = {
        "payload": dict(payload),
        "signature": signature
    }
    # User tries to grant themselves 10 extra years
    tampered_bundle["payload"]["expires_at"] = (now + timedelta(days=3650)).isoformat()

    is_valid_tampered, message_tampered = validate_license(
        public_key_b64=public_key_b64,
        license_bundle=tampered_bundle,
        expected_device_id=device_id
    )
    print(f"    Resultado: {'[FAIL] VALIDA' if is_valid_tampered else '[PASS] DETECTADA COMO INVALIDA'}")
    print(f"    Detalle:   {message_tampered}")
    assert is_valid_tampered is False

    # 6. Device Mismatch Test: License used on an unauthorized machine
    print("\n[5] Prueba de Dispositivo Ajeno (CASO DISPOSITIVO NO AUTORIZADO):")
    is_valid_device, message_device = validate_license(
        public_key_b64=public_key_b64,
        license_bundle=license_bundle,
        expected_device_id="DEV-UNAUTHORIZED-MACHINE-9999"
    )
    print(f"    Resultado: {'[FAIL] VALIDA' if is_valid_device else '[PASS] DETECTADA COMO RECHAZADA'}")
    print(f"    Detalle:   {message_device}")
    assert is_valid_device is False

    print("\n================================================================")
    print("[+] Todas las pruebas del nucleo criptografico pasaron con exito.")
    print("================================================================")


if __name__ == "__main__":
    run_demo()
