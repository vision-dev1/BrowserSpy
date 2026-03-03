"""
BrowserSpy — Saved passwords extractor.
Supports:
  - Chrome/Edge/Brave: AES-GCM decryption (v10/v11) or Windows DPAPI
  - Firefox: logins.json + key4.db via NSS (or base64 fallback)
"""

import base64
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from parsers.base import format_datetime, query_db, unix_to_datetime
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser
from utils.crypto import decrypt_chrome_password, get_chrome_master_key

logger = logging.getLogger(__name__)


@dataclass
class PasswordEntry:
    """Represents a single saved password record."""

    browser: str
    profile: str
    url: str
    username: str
    password: str
    date_created: str

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "date_created": self.date_created,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────

_CHROME_LOGINS_QUERY = """
    SELECT
        origin_url,
        username_value,
        password_value,
        date_created
    FROM logins
    WHERE blacklisted_by_user = 0
    ORDER BY date_created DESC
"""


def extract_chromium_passwords(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[PasswordEntry]:
    """
    Extract and decrypt saved passwords from Chromium-based browser profiles.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of PasswordEntry objects.
    """
    results: List[PasswordEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_login_db(profile)
        if db_path is None:
            logger.debug("No Login Data DB in profile: %s", profile)
            continue

        user_data_dir = parser.get_user_data_dir(profile)
        master_key = get_chrome_master_key(user_data_dir, browser=parser.browser)

        rows = query_db(db_path, _CHROME_LOGINS_QUERY)
        for row in rows:
            encrypted_pw = row["password_value"]
            password = decrypt_chrome_password(
                encrypted_pw,
                master_key=master_key,
                local_state_path=user_data_dir / "Local State",
                browser=parser.browser,
            )

            dt = None
            if row["date_created"]:
                from parsers.base import webkit_to_datetime
                dt = webkit_to_datetime(row["date_created"])

            entry = PasswordEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                url=row["origin_url"] or "",
                username=row["username_value"] or "",
                password=password,
                date_created=format_datetime(dt),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────


def _decrypt_firefox_password(encrypted_b64: str) -> str:
    """
    Attempt to decrypt a Firefox password stored in logins.json.

    Firefox uses NSS/PKCS#11 for encryption; full decryption requires
    the 'nss' or 'libnss3' library. This implementation uses a best-effort
    approach: if NSS bindings are unavailable, returns the raw base64 blob.

    Args:
        encrypted_b64: Base64-encoded encrypted password string.

    Returns:
        Decrypted password string, or '[NSS decryption unavailable]'.
    """
    # Try ctypes-based NSS decryption (Linux)
    if sys.platform.startswith("linux"):
        try:
            return _nss_decrypt_linux(encrypted_b64)
        except Exception as exc:
            logger.debug("NSS decryption failed: %s", exc)

    return f"[base64: {encrypted_b64[:30]}...]" if len(encrypted_b64) > 30 else f"[base64: {encrypted_b64}]"


def _nss_decrypt_linux(encrypted_b64: str) -> str:
    """
    Attempt NSS decryption on Linux using ctypes and libnss3.so.

    Args:
        encrypted_b64: Base64-encoded ciphertext.

    Returns:
        Decrypted string.

    Raises:
        Exception: If NSS library is unavailable or decryption fails.
    """
    import ctypes
    import ctypes.util

    nss_lib_name = ctypes.util.find_library("nss3")
    if not nss_lib_name:
        raise OSError("libnss3 not found on this system.")

    nss = ctypes.CDLL(nss_lib_name)

    # NSS structs
    class SECItem(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_uint),
            ("data", ctypes.c_char_p),
            ("len", ctypes.c_uint),
        ]

    # Initialize NSS (no-DB mode for structure; requires profile for real use)
    nss.NSS_NoDB_Init(b".")

    encrypted_bytes = base64.b64decode(encrypted_b64)
    decoded_der = base64.b64decode(encrypted_bytes)  # inner DER

    input_item = SECItem()
    input_item.data = ctypes.c_char_p(encrypted_bytes)
    input_item.len = len(encrypted_bytes)

    output_item = SECItem()

    result = nss.PK11SDR_Decrypt(
        ctypes.byref(input_item), ctypes.byref(output_item), None
    )

    if result != 0:
        raise RuntimeError("NSS PK11SDR_Decrypt failed.")

    return output_item.data[: output_item.len].decode("utf-8", errors="replace")


def extract_firefox_passwords(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[PasswordEntry]:
    """
    Extract saved passwords from Firefox profiles via logins.json.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of PasswordEntry objects.
    """
    results: List[PasswordEntry] = []

    for profile in parser.profiles:
        logins_path = parser.get_login_db(profile)
        if logins_path is None:
            logger.debug("No logins.json in profile: %s", profile)
            continue

        try:
            with open(logins_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning("Could not read logins.json: %s", exc)
            continue

        logins = data.get("logins", [])
        for login in logins:
            encrypted_pw = login.get("encryptedPassword", "")
            encrypted_user = login.get("encryptedUsername", "")
            password = _decrypt_firefox_password(encrypted_pw)
            username = _decrypt_firefox_password(encrypted_user)

            time_created = login.get("timeCreated", 0)
            dt = unix_to_datetime(time_created // 1000) if time_created else None

            entry = PasswordEntry(
                browser="Firefox",
                profile=profile.name,
                url=login.get("formSubmitURL") or login.get("hostname", ""),
                username=username,
                password=password,
                date_created=format_datetime(dt),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_passwords(entries: List[PasswordEntry]) -> None:
    """
    Display saved passwords in a rich terminal table.

    Args:
        entries: List of PasswordEntry objects.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    if not entries:
        console.print("[yellow][!] No saved passwords found.[/yellow]")
        return

    console.print(
        "[bold red]⚠  WARNING: Handle extracted passwords with extreme care![/bold red]\n"
    )

    table = Table(
        title=f"🔑 Saved Passwords ({len(entries)} entries)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Profile", style="blue")
    table.add_column("URL", style="white", max_width=40)
    table.add_column("Username", style="green")
    table.add_column("Password", style="bold red")
    table.add_column("Date Created", style="yellow")

    for e in entries:
        table.add_row(e.browser, e.profile, e.url, e.username, e.password, e.date_created)

    console.print(table)
