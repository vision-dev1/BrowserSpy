# Codes By Visionnn
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from parsers.base import (
    format_datetime,
    format_file_size,
    prtime_to_datetime,
    query_db,
    webkit_to_datetime,
)
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser
from utils.suspicious import is_suspicious_file

logger = logging.getLogger(__name__)


@dataclass
class DownloadEntry:
    """Represents a single download history record."""

    browser: str
    profile: str
    filename: str
    url: str
    save_path: str
    file_size: str
    start_time: str
    mime_type: str
    suspicious: bool = False

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "filename": self.filename,
            "url": self.url,
            "save_path": self.save_path,
            "file_size": self.file_size,
            "start_time": self.start_time,
            "mime_type": self.mime_type,
            "suspicious": self.suspicious,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────

_CHROME_DOWNLOADS_QUERY = """
    SELECT
        target_path,
        tab_url,
        total_bytes,
        start_time,
        mime_type
    FROM downloads
    ORDER BY start_time DESC
"""


def extract_chromium_downloads(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[DownloadEntry]:
    """
    Extract download history from Chromium-based browser profiles.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries to return.

    Returns:
        List of DownloadEntry objects.
    """
    results: List[DownloadEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_history_db(profile)
        if db_path is None:
            continue

        rows = query_db(db_path, _CHROME_DOWNLOADS_QUERY)
        for row in rows:
            target_path = row["target_path"] or ""
            filename = Path(target_path).name if target_path else "(unknown)"
            dt = webkit_to_datetime(row["start_time"])
            size_bytes = row["total_bytes"] or 0

            entry = DownloadEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                filename=filename,
                url=row["tab_url"] or "",
                save_path=target_path,
                file_size=format_file_size(size_bytes),
                start_time=format_datetime(dt),
                mime_type=row["mime_type"] or "",
                suspicious=is_suspicious_file(filename),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────

_FIREFOX_DOWNLOADS_QUERY = """
    SELECT
        p.url,
        p.title,
        a.content AS annotation_content,
        v.visit_date
    FROM moz_places p
    JOIN moz_historyvisits v ON p.id = v.place_id
    LEFT JOIN moz_annos a ON p.id = a.place_id
    WHERE a.anno_attribute_id IN (
        SELECT id FROM moz_anno_attributes WHERE name = 'downloads/destinationFileURI'
    )
    ORDER BY v.visit_date DESC
"""


def extract_firefox_downloads(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[DownloadEntry]:
    """
    Extract download history from Firefox profiles.

    Firefox stores downloads as annotated history entries in places.sqlite.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries to return.

    Returns:
        List of DownloadEntry objects.
    """
    results: List[DownloadEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_history_db(profile)
        if db_path is None:
            continue

        rows = query_db(db_path, _FIREFOX_DOWNLOADS_QUERY)
        for row in rows:
            save_path = (row["annotation_content"] or "").replace("file://", "")
            filename = Path(save_path).name if save_path else row["title"] or ""
            dt = prtime_to_datetime(row["visit_date"])

            entry = DownloadEntry(
                browser="Firefox",
                profile=profile.name,
                filename=filename,
                url=row["url"] or "",
                save_path=save_path,
                file_size="Unknown",
                start_time=format_datetime(dt),
                mime_type="",
                suspicious=is_suspicious_file(filename),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_downloads(entries: List[DownloadEntry], suspicious_only: bool = False) -> None:
    """
    Display download history in a rich terminal table.

    Args:
        entries: List of DownloadEntry objects.
        suspicious_only: If True, only show entries flagged as suspicious.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    filtered = [e for e in entries if e.suspicious] if suspicious_only else entries

    if not filtered:
        console.print("[yellow][!] No download entries to display.[/yellow]")
        return

    table = Table(
        title=f"⬇ Download History ({len(filtered)} entries)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Filename", style="white")
    table.add_column("URL", style="dim", max_width=40)
    table.add_column("Size", justify="right", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("MIME", style="dim")
    table.add_column("⚠", justify="center")

    for e in filtered:
        flag = "🔴" if e.suspicious else ""
        style = "red" if e.suspicious else ""
        table.add_row(
            e.browser, e.filename, e.url, e.file_size, e.start_time, e.mime_type, flag,
            style=style,
        )

    console.print(table)
