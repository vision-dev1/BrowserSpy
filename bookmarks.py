"""
BrowserSpy — Bookmarks parser.
Supports Chrome/Edge/Brave (Bookmarks JSON file) and Firefox (places.sqlite).
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from parsers.base import format_datetime, query_db, webkit_to_datetime
from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser

logger = logging.getLogger(__name__)


@dataclass
class BookmarkEntry:
    """Represents a single bookmark."""

    browser: str
    profile: str
    title: str
    url: str
    folder: str
    date_added: str

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "title": self.title,
            "url": self.url,
            "folder": self.folder,
            "date_added": self.date_added,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────


def _walk_bookmark_node(
    node: Dict[str, Any],
    folder_path: str,
    browser: str,
    profile_name: str,
) -> List[BookmarkEntry]:
    """
    Recursively walk a Chromium bookmarks JSON node tree.

    Args:
        node: Current bookmark node dict.
        folder_path: Current folder path string.
        browser: Browser display name.
        profile_name: Profile directory name.

    Returns:
        Flat list of BookmarkEntry objects.
    """
    results: List[BookmarkEntry] = []
    node_type = node.get("type")

    if node_type == "url":
        dt = webkit_to_datetime(int(node.get("date_added", 0)))
        results.append(
            BookmarkEntry(
                browser=browser,
                profile=profile_name,
                title=node.get("name", "(no title)"),
                url=node.get("url", ""),
                folder=folder_path,
                date_added=format_datetime(dt),
            )
        )
    elif node_type == "folder":
        folder_name = node.get("name", "Unnamed Folder")
        new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
        for child in node.get("children", []):
            results.extend(_walk_bookmark_node(child, new_path, browser, profile_name))

    return results


def extract_chromium_bookmarks(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[BookmarkEntry]:
    """
    Extract all bookmarks from Chromium-based browser profile JSON files.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of BookmarkEntry objects.
    """
    results: List[BookmarkEntry] = []

    for profile in parser.profiles:
        bm_file = parser.get_bookmarks_file(profile)
        if bm_file is None:
            continue

        try:
            with open(bm_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning("Cannot read Bookmarks file %s: %s", bm_file, exc)
            continue

        roots = data.get("roots", {})
        for root_name, root_node in roots.items():
            if isinstance(root_node, dict):
                entries = _walk_bookmark_node(root_node, root_name, parser.BROWSER_NAME, profile.name)
                results.extend(entries)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────

_FIREFOX_BOOKMARKS_QUERY = """
    SELECT
        b.title,
        p.url,
        b.dateAdded,
        parent_b.title AS folder_title
    FROM moz_bookmarks b
    JOIN moz_places p ON b.fk = p.id
    LEFT JOIN moz_bookmarks parent_b ON b.parent = parent_b.id
    WHERE b.type = 1
    ORDER BY b.dateAdded DESC
"""


def extract_firefox_bookmarks(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[BookmarkEntry]:
    """
    Extract bookmarks from Firefox profiles via places.sqlite.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of BookmarkEntry objects.
    """
    results: List[BookmarkEntry] = []

    for profile in parser.profiles:
        db_path = parser.get_bookmarks_file(profile)
        if db_path is None:
            continue

        rows = query_db(db_path, _FIREFOX_BOOKMARKS_QUERY)
        for row in rows:
            from parsers.base import prtime_to_datetime
            dt = prtime_to_datetime(row["dateAdded"])
            entry = BookmarkEntry(
                browser="Firefox",
                profile=profile.name,
                title=row["title"] or "(no title)",
                url=row["url"] or "",
                folder=row["folder_title"] or "Bookmarks",
                date_added=format_datetime(dt),
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_bookmarks(entries: List[BookmarkEntry]) -> None:
    """
    Display bookmarks in a rich terminal table.

    Args:
        entries: List of BookmarkEntry objects.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    if not entries:
        console.print("[yellow][!] No bookmarks to display.[/yellow]")
        return

    table = Table(
        title=f"🔖 Bookmarks ({len(entries)} entries)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Folder", style="blue", max_width=25)
    table.add_column("Title", style="white", max_width=35)
    table.add_column("URL", style="dim", max_width=50)
    table.add_column("Date Added", style="yellow")

    for e in entries:
        table.add_row(e.browser, e.folder, e.title, e.url, e.date_added)

    console.print(table)
