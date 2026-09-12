"""
guardian-license: Update Verification (Simplified OTA) Demo.

Demonstrates:
1. Fetching a signed update announcement from the server.
2. Case A: Validating an authentic file whose hash matches the signed checksum.
3. Case B: Detecting a corrupted/tampered file (hash mismatch).
4. Case C: Detecting a forged announcement (signature mismatch).
"""

import os
import sys

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

from server.crypto import generate_keypair
from server.updates import get_latest_release_signed, SIMULATED_VALID_PACKAGE
from update_verifier import verify_update_announcement, verify_downloaded_file

def run_ota_demo():
    print("================================================================")
    print("[*] GUARDIAN LICENSE — UPDATE VERIFICATION (OTA) DEMO")
    print("================================================================")

    # 1. Initialize Server Setup
    server_private_key, server_public_key = generate_keypair()
    from server.crypto import export_public_key_b64
    server_public_key_b64 = export_public_key_b64(server_public_key)

    print("\n[+] Simulando servidor anunciando nueva version...")
    payload, signature, pub_key = get_latest_release_signed(server_private_key, server_public_key_b64)
    
    print(f"    Version anunciada: {payload['version']}")
    print(f"    URL de descarga:   {payload['download_url']}")
    print(f"    Checksum SHA-256:  {payload['checksum_sha256']}")
    print(f"    Firma (parcial):   {signature[:20]}...")

    # =========================================================================
    # CASO A: Actualizacion exitosa
    # =========================================================================
    print("\n----------------------------------------------------------------")
    print("[+] CASO A: Cliente descarga paquete valido y sin alterar")
    print("----------------------------------------------------------------")

    # Paso 1: Verificar el anuncio
    is_valid_announcement, msg_announcement = verify_update_announcement(pub_key, payload, signature)
    print(f"    Verificando Anuncio: {'[PASS]' if is_valid_announcement else '[FAIL]'} {msg_announcement}")
    assert is_valid_announcement is True

    # Paso 2: Descargar (Simulado) y verificar el archivo
    print("    Simulando descarga de paquete...")
    downloaded_bytes_valid = SIMULATED_VALID_PACKAGE
    
    is_valid_file, msg_file = verify_downloaded_file(downloaded_bytes_valid, payload["checksum_sha256"])
    print(f"    Verificando Archivo: {'[PASS]' if is_valid_file else '[FAIL]'} {msg_file}")
    assert is_valid_file is True

    # =========================================================================
    # CASO B: Paquete modificado en transito (MitM en la descarga)
    # =========================================================================
    print("\n----------------------------------------------------------------")
    print("[-] CASO B: Atacante inyecta malware en el archivo descargado")
    print("----------------------------------------------------------------")

    # The announcement is still valid, but the file is tampered
    print("    Simulando descarga interceptada...")
    tampered_bytes = SIMULATED_VALID_PACKAGE + b" -- MALICIOUS PAYLOAD"
    
    is_valid_file_b, msg_file_b = verify_downloaded_file(tampered_bytes, payload["checksum_sha256"])
    print(f"    Verificando Archivo: {'[PASS]' if is_valid_file_b else '[FAIL]'}")
    print(f"    Mensaje: {msg_file_b}")
    assert is_valid_file_b is False

    # =========================================================================
    # CASO C: Anuncio falsificado (MitM en la API)
    # =========================================================================
    print("\n----------------------------------------------------------------")
    print("[-] CASO C: Atacante intenta falsificar la URL de descarga")
    print("----------------------------------------------------------------")

    # Attacker alters the URL in the payload, but doesn't have the server's private key
    forged_payload = payload.copy()
    forged_payload["download_url"] = "http://evil-attacker.local/malware.zip"
    
    # Client attempts to verify the signature against the forged payload
    is_valid_announcement_c, msg_announcement_c = verify_update_announcement(pub_key, forged_payload, signature)
    print(f"    Verificando Anuncio: {'[PASS]' if is_valid_announcement_c else '[FAIL]'}")
    print(f"    Mensaje: {msg_announcement_c}")
    assert is_valid_announcement_c is False

    print("\n================================================================")
    print("[+] Demostracion de Verificacion OTA completada exitosamente.")
    print("================================================================")

if __name__ == "__main__":
    run_ota_demo()
