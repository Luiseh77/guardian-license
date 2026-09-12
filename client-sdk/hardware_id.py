"""
guardian-license Client SDK: Hardware Fingerprinting and Machine Binding.

Generates a deterministic device identifier (hardware_id) based on system
parameters (MAC address, disk serial, hostname) using SHA-256 hashing.
"""

import hashlib
import platform
import socket
import uuid
from typing import Optional


def compute_hardware_hash(mac_address: str, disk_serial: str, hostname: str) -> str:
    """
    Computes a deterministic SHA-256 hardware identifier from machine parameters.
    
    Returns a standardized identifier in the format:
    DEV-{8_HEX}-{8_HEX}-{8_HEX} (e.g. DEV-89A1B2C3-D4E5F678-90123456)
    """
    raw_components = f"{mac_address.strip().lower()}|{disk_serial.strip()}|{hostname.strip().lower()}"
    digest = hashlib.sha256(raw_components.encode("utf-8")).hexdigest()
    
    return f"DEV-{digest[:8].upper()}-{digest[8:16].upper()}-{digest[16:24].upper()}"


def get_current_hardware_id(simulated_disk_serial: Optional[str] = None) -> str:
    """
    Collects current machine parameters using portable Python standard libraries
    and returns the deterministic hardware fingerprint.
    
    ARCHITECTURE NOTE:
    In production environments, retrieving tamper-resistant hardware serial numbers
    (e.g., motherboard UUID, physical drive serials via SMART) requires low-level 
    platform APIs or specialized libraries:
      - Windows: `wmi` (Win32_BaseBoard / Win32_DiskDrive) or PowerShell WMI calls.
      - Linux: `/etc/machine-id` or `udev` / `lsblk --nodeps -no serial`.
      - macOS: `ioreg -rd1 -c IOPlatformExpertDevice`.
      
    For portable cross-platform demonstration, this module combines the system's
    primary MAC address (`uuid.getnode()`), network hostname (`socket.gethostname()`),
    and a platform signature or simulated disk serial.

    Note: On some Linux distributions, `platform.processor()` may return an empty
    string; `platform.machine()` is included to guarantee a consistent fallback signature.
    """
    # 1. Primary MAC address
    mac_node = uuid.getnode()
    mac_address = ":".join(f"{(mac_node >> i) & 0xFF:02x}" for i in range(0, 48, 8)[::-1])

    # 2. Hostname
    hostname = socket.gethostname()

    # 3. Disk / system signature (robust against empty processor strings on Linux)
    cpu_sig = platform.processor().strip()[:12] if platform.processor() else "generic-cpu"
    disk_serial = simulated_disk_serial or f"DSK-{platform.machine()}-{platform.system()}-{cpu_sig}"

    return compute_hardware_hash(mac_address, disk_serial, hostname)
