"""
guardian-license: Hardware Binding Verification Demo.

Demonstrates:
1. Deterministic hardware ID generation from machine parameters.
2. Case A: Authentic license running on the authorized device (Pass).
3. Case B: Same license copied to a different unauthorized machine (Rejected by Hardware Mismatch).
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

# Add project root and client-sdk to Python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "client-sdk"))

from server.crypto import generate_keypair, export_public_key_b64, sign_payload
from verifier import validate_license
from hardware_id import compute_hardware_hash, get_current_hardware_id


def run_hardware_demo():
    print("================================================================")
    print("[*] GUARDIAN LICENSE — HARDWARE BINDING DEMO")
    print("================================================================")

    # 1. Setup Server and Keys
    server_private_key, server_public_key = generate_keypair()
    public_key_b64 = export_public_key_b64(server_public_key)
    print(f"\n[1] Servidor inicializado con clave publica Ed25519.")

    # 2. Define two distinct machines with simulated hardware components
    # Machine A: Authorized workstation (Buyer's licensed machine)
    mac_a = "00:1A:2B:3C:4D:5E"
    disk_a = "WD-WCC4M2345678"
    host_a = "WORKSTATION-PROD-01"
    device_id_a = compute_hardware_hash(mac_a, disk_a, host_a)

    print(f"\n[2] Maquina A (Dispositivo Autorizado):")
    print(f"    - MAC:        {mac_a}")
    print(f"    - Serial HD:  {disk_a}")
    print(f"    - Hostname:   {host_a}")
    print(f"    -> Hardware ID: {device_id_a}")

    # Machine B: Unauthorized laptop (Attacker trying to copy the software)
    mac_b = "A4:83:E7:99:11:22"
    disk_b = "NVME-SAMSUNG-980PRO"
    host_b = "LAPTOP-EXTERNAL-02"
    device_id_b = compute_hardware_hash(mac_b, disk_b, host_b)

    print(f"\n[3] Maquina B (Dispositivo No Autorizado / Copia Pirata):")
    print(f"    - MAC:        {mac_b}")
    print(f"    - Serial HD:  {disk_b}")
    print(f"    - Hostname:   {host_b}")
    print(f"    -> Hardware ID: {device_id_b}")

    # 3. Server issues license specifically bound to Machine A
    now = datetime.now(timezone.utc)
    payload = {
        "license_id": "LIC-ENT-77890",
        "product_name": "GuardianLicense Demo",
        "device_id": device_id_a,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(days=60)).isoformat()
    }
    signature = sign_payload(server_private_key, payload)
    license_bundle = {
        "payload": payload,
        "signature": signature
    }

    print("\n[4] Licencia emitida por el servidor (Atada a Maquina A):")
    print(json.dumps(license_bundle, indent=2))

    # 4. Case A: Run software on Authorized Machine A
    print("\n[5] CASO A: Ejecutando software en la Maquina Autorizada (A)...")
    is_valid_a, msg_a = validate_license(
        public_key_b64=public_key_b64,
        license_bundle=license_bundle,
        expected_device_id=device_id_a
    )
    print(f"    Resultado: {'[PASS] LICENCIA ACTIVA' if is_valid_a else '[FAIL] RECHAZADA'}")
    print(f"    Detalle:   {msg_a}")
    assert is_valid_a is True

    # 5. Case B: Copy exact same license bundle to Unauthorized Machine B
    print("\n[6] CASO B: La misma licencia se copia e intenta ejecutar en Maquina B...")
    is_valid_b, msg_b = validate_license(
        public_key_b64=public_key_b64,
        license_bundle=license_bundle,
        expected_device_id=device_id_b
    )
    print(f"    Resultado: {'[FAIL] LICENCIA ACTIVA' if is_valid_b else '[PASS] BLOQUEADA EXITOSAMENTE'}")
    print(f"    Detalle:   {msg_b}")
    assert is_valid_b is False

    # 6. Current Host Inspection
    current_id = get_current_hardware_id()
    print(f"\n[7] Huella de Hardware del equipo local actual:")
    print(f"    -> {current_id}")

    print("\n================================================================")
    print("[+] Demostracion de Hardware Binding completada exitosamente.")
    print("================================================================")


if __name__ == "__main__":
    run_hardware_demo()

