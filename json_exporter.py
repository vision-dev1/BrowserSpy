"""
BrowserSpy — JSON exporter.
Serializes all extracted browser artifacts into a pretty-printed JSON report.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def export_json(data: Dict[str, Any], output_file: str) -> None:
    """
    Export all browser extraction results to a JSON file.

    The data dictionary should have the structure:
        {
            "metadata": {...},
            "chrome": { "history": [...], "cookies": [...], ... },
            "firefox": { "history": [...], ... },
            ...
        }

    Args:
        data: Dictionary containing all extracted browser data.
        output_file: Destination file path (e.g., 'report.json').
    """
    output_path = Path(output_file)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info("JSON report saved to: %s", output_path.resolve())
        from utils.colors import success
        success(f"JSON report saved → {output_path.resolve()}")
    except OSError as exc:
        logger.error("Failed to write JSON file: %s", exc)
        from utils.colors import error
        error(f"Could not write JSON file: {exc}")


def build_export_dict(
    browser: str,
    history: List[Any] = None,
    downloads: List[Any] = None,
    passwords: List[Any] = None,
    cookies: List[Any] = None,
    autofill: List[Any] = None,
    extensions: List[Any] = None,
    bookmarks: List[Any] = None,
    searches: List[Any] = None,
) -> Dict[str, Any]:
    """
    Build a structured export dictionary for a single browser.

    Args:
        browser: Browser name string.
        history: List of HistoryEntry objects (or dicts).
        downloads: List of DownloadEntry objects.
        passwords: List of PasswordEntry objects.
        cookies: List of CookieEntry objects.
        autofill: List of AutofillEntry objects.
        extensions: List of ExtensionEntry objects.
        bookmarks: List of BookmarkEntry objects.
        searches: List of SearchEntry objects.

    Returns:
        Structured dict ready for JSON serialization.
    """

    def _serialize(items: List[Any]) -> List[dict]:
        if not items:
            return []
        return [item.to_dict() if hasattr(item, "to_dict") else item for item in items]

    return {
        "browser": browser,
        "history": _serialize(history or []),
        "downloads": _serialize(downloads or []),
        "passwords": _serialize(passwords or []),
        "cookies": _serialize(cookies or []),
        "autofill": _serialize(autofill or []),
        "extensions": _serialize(extensions or []),
        "bookmarks": _serialize(bookmarks or []),
        "searches": _serialize(searches or []),
    }
