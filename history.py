"""
BrowserSpy — Browsing history extractor.
Supports Chrome/Edge/Brave (SQLite History DB) and Firefox (places.sqlite).
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from parsers.base import (
    format_datetime,
    prtime_to_datetime,
    query_db,
    webkit_to_datetime,
)
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser
from utils.suspicious import flag_suspicious_url

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """Represents a single browsing history record."""

    browser: str
    profile: str
    url: str
    title: str
    visit_count: int
    last_visit_time: str
    suspicious: bool = False

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "url": self.url,
            "title": self.title,
            "visit_count": self.visit_count,
            "last_visit_time": self.last_visit_time,
            "suspicious": self.suspicious,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────

_CHROME_HISTORY_QUERY = """
    SELECT
        urls.url,
        urls.title,
        urls.visit_count,
        urls.last_visit_time
    FROM urls
    ORDER BY last_visit_time DESC
"""


def extract_chromium_history(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    Extract browsing history from all Chromium-family browser profiles.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries to return (per profile).

    Returns:
        List of HistoryEntry objects.
    """
    results: List[HistoryEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_history_db(profile)
        if db_path is None:
            logger.debug("No history DB in profile: %s", profile)
            continue

        rows = query_db(db_path, _CHROME_HISTORY_QUERY)
        for row in rows:
            dt = webkit_to_datetime(row["last_visit_time"])
            entry = HistoryEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                url=row["url"] or "",
                title=row["title"] or "(no title)",
                visit_count=row["visit_count"] or 0,
                last_visit_time=format_datetime(dt),
                suspicious=flag_suspicious_url(row["url"] or ""),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────

_FIREFOX_HISTORY_QUERY = """
    SELECT
        p.url,
        p.title,
        p.visit_count,
        MAX(v.visit_date) AS last_visit_time
    FROM moz_places p
    LEFT JOIN moz_historyvisits v ON p.id = v.place_id
    WHERE p.hidden = 0
    GROUP BY p.id
    ORDER BY last_visit_time DESC
"""


def extract_firefox_history(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    Extract browsing history from all Firefox profiles.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries to return (per profile).

    Returns:
        List of HistoryEntry objects.
    """
    results: List[HistoryEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_history_db(profile)
        if db_path is None:
            logger.debug("No places.sqlite in profile: %s", profile)
            continue

        rows = query_db(db_path, _FIREFOX_HISTORY_QUERY)
        for row in rows:
            dt = prtime_to_datetime(row["last_visit_time"])
            entry = HistoryEntry(
                browser="Firefox",
                profile=profile.name,
                url=row["url"] or "",
                title=row["title"] or "(no title)",
                visit_count=row["visit_count"] or 0,
                last_visit_time=format_datetime(dt),
                suspicious=flag_suspicious_url(row["url"] or ""),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_history(entries: List[HistoryEntry], suspicious_only: bool = False) -> None:
    """
    Display browsing history in a rich terminal table.

    Args:
        entries: List of HistoryEntry objects.
        suspicious_only: If True, only show entries flagged as suspicious.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    filtered = [e for e in entries if e.suspicious] if suspicious_only else entries
    if not filtered:
        console.print("[yellow][!] No history entries to display.[/yellow]")
        return

    table = Table(
        title=f"🕒 Browsing History ({len(filtered)} entries)",
        box=box.ROUNDED,
        show_lines=False,
        highlight=True,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Profile", style="blue", no_wrap=True)
    table.add_column("Title", style="white", max_width=35)
    table.add_column("URL", style="dim", max_width=50)
    table.add_column("Visits", justify="right", style="green")
    table.add_column("Last Visit", style="yellow")
    table.add_column("⚠", justify="center")

    for entry in filtered:
        flag = "🔴" if entry.suspicious else ""
        style = "red" if entry.suspicious else ""
        table.add_row(
            entry.browser,
            entry.profile,
            entry.title,
            entry.url,
            str(entry.visit_count),
            entry.last_visit_time,
            flag,
            style=style,
        )

    console.print(table)
