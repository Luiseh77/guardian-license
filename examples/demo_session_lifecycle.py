"""
guardian-license: Session Lifecycle and Expiration Lockout Demo.

Demonstrates:
1. Short-lived session creation (TTL in seconds for quick demo execution).
2. Case A: Continuous periodic heartbeat renewal keeping the client alive.
3. Case B: Heartbeat interruption causing session expiration and triggering
   an immediate application lockout (SessionExpiredError / LockOverlay).
"""

from datetime import datetime, timezone
import sys
import time
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

from server.crypto import generate_keypair
from server.sessions import SessionStore
from session import SessionManager, SessionExpiredError


def run_session_demo():
    print("================================================================")
    print("[*] GUARDIAN LICENSE — SESSION LIFECYCLE & LOCKOUT DEMO")
    print("================================================================")

    # 1. Initialize server state and demo cryptographic keypair
    server_private_key, server_public_key = generate_keypair()
    from server.crypto import export_public_key_b64
    server_public_key_b64 = export_public_key_b64(server_public_key)
    server_sessions = SessionStore()

    license_id = "LIC-ENTERPRISE-5544"
    device_id = "DEV-3835E6E0-294B49F7-70595D0F"

    # Fast demonstration parameters: 1.5s TTL, 1.5s extension, heartbeats every 0.5s
    SESSION_TTL_SECONDS = 2
    HEARTBEAT_EXTEND_SECONDS = 2

    # Helper function simulating client-to-server heartbeat request
    def server_heartbeat_api(ses_id: str, ses_token: str):
        success, record, token, msg = server_sessions.process_heartbeat(
            session_id=ses_id,
            session_token=ses_token,
            extend_seconds=HEARTBEAT_EXTEND_SECONDS,
            server_private_key=server_private_key,
            server_public_key_b64=server_public_key_b64
        )
        expiry_iso = record.expires_at.isoformat() if record else None
        return success, record, token, expiry_iso

    # 2. Client initiates a new session
    print(f"\n[1] Iniciando sesion de corta duracion (TTL = {SESSION_TTL_SECONDS}s)...")
    record, initial_token = server_sessions.create_session(
        license_id=license_id,
        device_id=device_id,
        ttl_seconds=SESSION_TTL_SECONDS,
        server_private_key=server_private_key
    )

    client_session = SessionManager(device_id=device_id)
    client_session.initialize_session(
        session_id=record.session_id,
        session_token=initial_token,
        expires_at_iso=record.expires_at.isoformat()
    )

    print(f"    Session ID:  {client_session.session_id}")
    print(f"    Token:       {client_session.session_token[:30]}...")
    print(f"    Expira en:   {client_session.seconds_remaining():.2f}s")
    print(f"    Estado:      {'[PASS] ACTIVA' if client_session.is_session_valid() else '[FAIL] EXPIRADA'}")

    # =========================================================================
    # CASO A: Heartbeats exitosos a tiempo
    # =========================================================================
    print("\n----------------------------------------------------------------")
    print("[+] CASO A: Cliente ejecutando renovaciones periodicas (Heartbeat)")
    print("----------------------------------------------------------------")

    for cycle in range(1, 4):
        time.sleep(0.6)  # Wait 600ms (well within the 2s TTL)
        client_session.assert_active()  # Application operation authorized
        
        # Send heartbeat to server
        success, _, new_token, new_expiry = server_heartbeat_api(client_session.session_id, client_session.session_token)
        assert success is True
        client_session.apply_heartbeat_renewal(new_token, new_expiry)

        print(f"    -> Heartbeat #{cycle} exitoso. Tiempo restante renovado: {client_session.seconds_remaining():.2f}s")

    print("    Resultado Caso A: [PASS] La aplicacion se mantuvo activa y operativa.")

    # =========================================================================
    # CASO B: Perdida de conexion / Omision de Heartbeat -> Bloqueo
    # =========================================================================
    print("\n----------------------------------------------------------------")
    print("[-] CASO B: Omision de Heartbeat (Simulando perdida de conexion)")
    print("----------------------------------------------------------------")

    print(f"    Esperando {SESSION_TTL_SECONDS + 0.5:.1f}s sin enviar heartbeat...")
    time.sleep(SESSION_TTL_SECONDS + 0.5)

    print(f"    Tiempo restante: {client_session.seconds_remaining():.2f}s")
    print(f"    Evaluacion de validez: {client_session.is_session_valid()}")

    # 1. Client attempts an operation without active session
    print("\n    Intentando ejecutar una accion de software protegida...")
    try:
        client_session.assert_active()
        print("    [FAIL] ERROR: La accion debio ser bloqueada.")
        assert False
    except SessionExpiredError as err:
        print("    " + "=" * 56)
        print("    [LOCKOUT DETECTADO] PANTALLA DE BLOQUEO ACTIVADA")
        print(f"    Detalle: {err}")
        print("    " + "=" * 56)

    # 2. Late heartbeat rejected by server
    print("\n    Cliente tardio intenta enviar heartbeat al servidor despues de expirar...")
    success_late, _, _, msg_late = server_sessions.process_heartbeat(
        session_id=client_session.session_id,
        session_token=client_session.session_token,
        extend_seconds=HEARTBEAT_EXTEND_SECONDS,
        server_private_key=server_private_key,
        server_public_key_b64=server_public_key_b64
    )
    print(f"    Respuesta Servidor: [PASS] RECHAZADO (Success={success_late})")
    print(f"    Mensaje:            {msg_late}")
    assert success_late is False

    print("\n================================================================")
    print("[+] Demostracion de Ciclo de Sesiones y Bloqueo completada.")
    print("================================================================")


if __name__ == "__main__":
    run_session_demo()
