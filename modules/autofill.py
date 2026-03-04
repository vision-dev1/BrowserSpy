# Codes By Visionnn
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from parsers.base import format_datetime, query_db, unix_to_datetime, webkit_to_datetime
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser

logger = logging.getLogger(__name__)


@dataclass
class AutofillEntry:
    """Represents a single autofill / form data record."""

    browser: str
    profile: str
    field_name: str
    value: str
    count: int
    date_last_used: str

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "field_name": self.field_name,
            "value": self.value,
            "count": self.count,
            "date_last_used": self.date_last_used,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────

_CHROME_AUTOFILL_QUERY = """
    SELECT
        name,
        value,
        count,
        date_last_used
    FROM autofill
    ORDER BY count DESC
"""


def extract_chromium_autofill(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[AutofillEntry]:
    """
    Extract autofill/form data from Chromium-based browser profiles.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of AutofillEntry objects.
    """
    results: List[AutofillEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_web_data_db(profile)
        if db_path is None:
            logger.debug("No Web Data DB in profile: %s", profile)
            continue

        rows = query_db(db_path, _CHROME_AUTOFILL_QUERY)
        for row in rows:
            dt = unix_to_datetime(row["date_last_used"])
            entry = AutofillEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                field_name=row["name"] or "",
                value=row["value"] or "",
                count=row["count"] or 0,
                date_last_used=format_datetime(dt),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────

_FIREFOX_FORMHISTORY_QUERY = """
    SELECT
        fieldname,
        value,
        timesUsed,
        lastUsed
    FROM moz_formhistory
    ORDER BY timesUsed DESC
"""


def extract_firefox_autofill(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[AutofillEntry]:
    """
    Extract autofill/form data from Firefox profiles via formhistory.sqlite.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of AutofillEntry objects.
    """
    results: List[AutofillEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_form_history_db(profile)
        if db_path is None:
            logger.debug("No formhistory.sqlite in profile: %s", profile)
            continue

        rows = query_db(db_path, _FIREFOX_FORMHISTORY_QUERY)
        for row in rows:
            from parsers.base import prtime_to_datetime
            dt = prtime_to_datetime(row["lastUsed"])
            entry = AutofillEntry(
                browser="Firefox",
                profile=profile.name,
                field_name=row["fieldname"] or "",
                value=row["value"] or "",
                count=row["timesUsed"] or 0,
                date_last_used=format_datetime(dt),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_autofill(entries: List[AutofillEntry]) -> None:
    """
    Display autofill data in a rich terminal table.

    Args:
        entries: List of AutofillEntry objects.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    if not entries:
        console.print("[yellow][!] No autofill data found.[/yellow]")
        return

    table = Table(
        title=f"📝 Autofill / Form Data ({len(entries)} entries)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Profile", style="blue")
    table.add_column("Field Name", style="white")
    table.add_column("Value", style="green", max_width=40)
    table.add_column("Used", justify="right", style="yellow")
    table.add_column("Last Used", style="dim")

    for e in entries:
        table.add_row(
            e.browser, e.profile, e.field_name, e.value, str(e.count), e.date_last_used
        )

    console.print(table)
