"""
BrowserSpy — Search query extractor.
Parses browsing history URLs to extract past search queries from
Google, Bing, DuckDuckGo, Yahoo, and other popular search engines.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from modules.history import HistoryEntry

logger = logging.getLogger(__name__)


@dataclass
class SearchEntry:
    """Represents a single extracted search query."""

    browser: str
    profile: str
    engine: str
    query: str
    url: str
    timestamp: str

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "engine": self.engine,
            "query": self.query,
            "url": self.url,
            "timestamp": self.timestamp,
        }


# ─── Search engine patterns ───────────────────────────────────────────────────

# Each entry maps a domain pattern to (engine_name, query_param)
_SEARCH_ENGINES: Dict[str, tuple] = {
    "google.com/search": ("Google", "q"),
    "google.": ("Google", "q"),
    "bing.com/search": ("Bing", "q"),
    "search.yahoo.com": ("Yahoo", "p"),
    "duckduckgo.com": ("DuckDuckGo", "q"),
    "yandex.com/search": ("Yandex", "text"),
    "yandex.ru/search": ("Yandex", "text"),
    "search.brave.com": ("Brave Search", "q"),
    "ecosia.org/search": ("Ecosia", "q"),
    "startpage.com": ("Startpage", "query"),
    "search.aol.com": ("AOL", "q"),
    "ask.com": ("Ask", "q"),
    "baidu.com/s": ("Baidu", "wd"),
}


def _extract_query_from_url(url: str) -> Optional[tuple]:
    """
    Attempt to extract a search engine name and query string from a URL.

    Args:
        url: URL string to parse.

    Returns:
        Tuple of (engine_name, query_string) or None if not a search URL.
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        host_path = (parsed.netloc + parsed.path).lower()

        for pattern, (engine, param) in _SEARCH_ENGINES.items():
            if pattern in host_path:
                params = parse_qs(parsed.query)
                query_values = params.get(param, [])
                if query_values:
                    return (engine, query_values[0])
    except Exception as exc:
        logger.debug("URL parse error for %s: %s", url, exc)

    return None


def extract_searches_from_history(
    history_entries: List[HistoryEntry],
    limit: Optional[int] = None,
) -> List[SearchEntry]:
    """
    Extract search queries by analyzing browsing history URLs.

    Args:
        history_entries: List of HistoryEntry objects from the history module.
        limit: Maximum number of search entries to return.

    Returns:
        List of SearchEntry objects.
    """
    results: List[SearchEntry] = []

    for entry in history_entries:
        match = _extract_query_from_url(entry.url)
        if match is None:
            continue

        engine, query = match
        if not query.strip():
            continue

        search = SearchEntry(
            browser=entry.browser,
            profile=entry.profile,
            engine=engine,
            query=query,
            url=entry.url,
            timestamp=entry.last_visit_time,
        )
        results.append(search)

    if limit:
        results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_searches(entries: List[SearchEntry]) -> None:
    """
    Display search queries in a rich terminal table.

    Args:
        entries: List of SearchEntry objects.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    if not entries:
        console.print("[yellow][!] No search queries found.[/yellow]")
        return

    table = Table(
        title=f"🔍 Search Queries ({len(entries)} entries)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Engine", style="magenta")
    table.add_column("Query", style="bold white", max_width=60)
    table.add_column("Timestamp", style="yellow")

    for e in entries:
        table.add_row(e.browser, e.engine, e.query, e.timestamp)

    console.print(table)
