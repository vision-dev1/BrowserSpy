"""
BrowserSpy — CSV exporter.
Exports each artifact type to a separate CSV file.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _serialize(items: List[Any]) -> List[dict]:
    """Convert a list of entry objects to a list of plain dicts."""
    return [item.to_dict() if hasattr(item, "to_dict") else item for item in items]


def _write_csv(records: List[dict], output_path: Path) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Args:
        records: List of dicts — all must share the same keys.
        output_path: Destination file path.
    """
    if not records:
        logger.debug("No records to write for %s — skipping.", output_path)
        return

    fieldnames = list(records[0].keys())
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        from utils.colors import success
        success(f"CSV saved → {output_path.resolve()}")
    except OSError as exc:
        from utils.colors import error
        error(f"Could not write CSV file {output_path}: {exc}")


def export_csv(data: Dict[str, Any], output_prefix: str = "browserspy") -> None:
    """
    Export all browser artifacts to separate CSV files.

    Creates one CSV file per artifact type, e.g.:
      - browserspy_history.csv
      - browserspy_cookies.csv
      - browserspy_passwords.csv
      - etc.

    Args:
        data: Dictionary of browser data (same structure as JSON export).
        output_prefix: File name prefix (without extension).
    """
    artifact_keys = [
        "history",
        "downloads",
        "passwords",
        "cookies",
        "autofill",
        "extensions",
        "bookmarks",
        "searches",
    ]

    # Aggregate all entries across browsers for each artifact type
    aggregated: Dict[str, List[dict]] = {key: [] for key in artifact_keys}

    # data may be a list of per-browser dicts OR a single dict
    browser_records = data if isinstance(data, list) else [data]
    for browser_data in browser_records:
        for key in artifact_keys:
            items = browser_data.get(key, [])
            serialized = _serialize(items)
            aggregated[key].extend(serialized)

    # Write one CSV file per artifact type
    for key, records in aggregated.items():
        if records:
            output_path = Path(f"{output_prefix}_{key}.csv")
            _write_csv(records, output_path)
