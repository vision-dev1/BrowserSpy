"""
BrowserSpy — Cookie extractor.
Supports Chrome/Edge/Brave (Cookies SQLite DB) and Firefox (cookies.sqlite).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from parsers.base import format_datetime, query_db, unix_to_datetime, webkit_to_datetime
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser
from utils.suspicious import is_high_value_domain, is_session_cookie

logger = logging.getLogger(__name__)


@dataclass
class CookieEntry:
    """Represents a single browser cookie record."""

    browser: str
    profile: str
    domain: str
    name: str
    value: str
    path: str
    expires: str
    secure: bool
    http_only: bool
    high_value: bool = False
    session_token: bool = False

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "domain": self.domain,
            "name": self.name,
            "value": self.value,
            "path": self.path,
            "expires": self.expires,
            "secure": self.secure,
            "http_only": self.http_only,
            "high_value": self.high_value,
            "session_token": self.session_token,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────

_CHROME_COOKIES_QUERY = """
    SELECT
        host_key,
        name,
        value,
        path,
        expires_utc,
        is_secure,
        is_httponly
    FROM cookies
    ORDER BY expires_utc DESC
"""


def extract_chromium_cookies(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[CookieEntry]:
    """
    Extract cookies from Chromium-based browser profiles.

    Note: Chrome 80+ encrypts cookie values using AES-GCM.
    This extractor reads the (possibly empty) unencrypted 'value' column.
    Full decryption requires integration with the master key (see crypto.py).

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of CookieEntry objects.
    """
    results: List[CookieEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_cookies_db(profile)
        if db_path is None:
            logger.debug("No cookies DB in profile: %s", profile)
            continue

        rows = query_db(db_path, _CHROME_COOKIES_QUERY)
        for row in rows:
            domain = row["host_key"] or ""
            name = row["name"] or ""
            value = row["value"] or "[encrypted]"
            dt = webkit_to_datetime(row["expires_utc"])

            entry = CookieEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                domain=domain,
                name=name,
                value=value if value else "[encrypted]",
                path=row["path"] or "/",
                expires=format_datetime(dt),
                secure=bool(row["is_secure"]),
                http_only=bool(row["is_httponly"]),
                high_value=is_high_value_domain(domain),
                session_token=is_session_cookie(name, value),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────

_FIREFOX_COOKIES_QUERY = """
    SELECT
        host,
        name,
        value,
        path,
        expiry,
        isSecure,
        isHttpOnly
    FROM moz_cookies
    ORDER BY expiry DESC
"""


def extract_firefox_cookies(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[CookieEntry]:
    """
    Extract cookies from Firefox profiles.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of CookieEntry objects.
    """
    results: List[CookieEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_cookies_db(profile)
        if db_path is None:
            continue

        rows = query_db(db_path, _FIREFOX_COOKIES_QUERY)
        for row in rows:
            domain = row["host"] or ""
            name = row["name"] or ""
            value = row["value"] or ""
            dt = unix_to_datetime(row["expiry"])

            entry = CookieEntry(
                browser="Firefox",
                profile=profile.name,
                domain=domain,
                name=name,
                value=value,
                path=row["path"] or "/",
                expires=format_datetime(dt),
                secure=bool(row["isSecure"]),
                http_only=bool(row["isHttpOnly"]),
                high_value=is_high_value_domain(domain),
                session_token=is_session_cookie(name, value),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_cookies(entries: List[CookieEntry], suspicious_only: bool = False) -> None:
    """
    Display cookies in a rich terminal table.

    Args:
        entries: List of CookieEntry objects.
        suspicious_only: If True, show only high-value or session-token cookies.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    if suspicious_only:
        filtered = [e for e in entries if e.high_value or e.session_token]
    else:
        filtered = entries

    if not filtered:
        console.print("[yellow][!] No cookie entries to display.[/yellow]")
        return

    table = Table(
        title=f"🍪 Cookies ({len(filtered)} entries)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Domain", style="white", max_width=30)
    table.add_column("Name", style="blue", max_width=25)
    table.add_column("Value", style="dim", max_width=25)
    table.add_column("Expires", style="yellow")
    table.add_column("Sec", justify="center")
    table.add_column("HTTP", justify="center")
    table.add_column("HV", justify="center")
    table.add_column("Sess", justify="center")

    for e in filtered:
        style = "bold red" if e.high_value else ("yellow" if e.session_token else "")
        table.add_row(
            e.browser,
            e.domain,
            e.name,
            e.value[:25] + "…" if len(e.value) > 25 else e.value,
            e.expires,
            "✔" if e.secure else "",
            "✔" if e.http_only else "",
            "🔴" if e.high_value else "",
            "🟡" if e.session_token else "",
            style=style,
        )

    console.print(table)
