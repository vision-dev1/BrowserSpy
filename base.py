"""
BrowserSpy — Base parser.
Provides shared SQLite database helpers, timestamp conversion utilities,
and the abstract base class that all browser parsers inherit from.
"""

import abc
import logging
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Timestamp conversion constants ───────────────────────────────────────────

# Chrome/Edge/Brave: microseconds since 1601-01-01 00:00:00 UTC
_WEBKIT_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
_WEBKIT_EPOCH_UNIX_MICROS = 11644473600 * 1_000_000  # difference in microseconds

# Firefox: microseconds since 1970-01-01 (PRTime)
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


# ─── Timestamp helpers ─────────────────────────────────────────────────────────


def webkit_to_datetime(webkit_timestamp: int) -> Optional[datetime]:
    """
    Convert a WebKit timestamp (microseconds since 1601-01-01) to a local datetime.

    Args:
        webkit_timestamp: Integer WebKit timestamp.

    Returns:
        Localized datetime object, or None if the timestamp is invalid.
    """
    if not webkit_timestamp or webkit_timestamp == 0:
        return None
    try:
        unix_micros = webkit_timestamp - _WEBKIT_EPOCH_UNIX_MICROS
        unix_seconds = unix_micros / 1_000_000
        dt = datetime.fromtimestamp(unix_seconds, tz=timezone.utc)
        return dt.astimezone()
    except (OverflowError, OSError, ValueError):
        return None


def prtime_to_datetime(prtime: int) -> Optional[datetime]:
    """
    Convert a Firefox PRTime timestamp (microseconds since Unix epoch) to local datetime.

    Args:
        prtime: Integer PRTime value.

    Returns:
        Localized datetime object, or None if invalid.
    """
    if not prtime or prtime == 0:
        return None
    try:
        unix_seconds = prtime / 1_000_000
        dt = datetime.fromtimestamp(unix_seconds, tz=timezone.utc)
        return dt.astimezone()
    except (OverflowError, OSError, ValueError):
        return None


def unix_to_datetime(unix_timestamp: int) -> Optional[datetime]:
    """
    Convert a standard Unix timestamp (seconds since epoch) to local datetime.

    Args:
        unix_timestamp: Unix timestamp integer or float.

    Returns:
        Localized datetime object, or None if invalid.
    """
    if not unix_timestamp or unix_timestamp == 0:
        return None
    try:
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        return dt.astimezone()
    except (OverflowError, OSError, ValueError):
        return None


def format_datetime(dt: Optional[datetime]) -> str:
    """
    Format a datetime object as a readable string.

    Args:
        dt: datetime object to format.

    Returns:
        Formatted string, or 'N/A' if dt is None.
    """
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_file_size(size_bytes: int) -> str:
    """
    Convert a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string (e.g., '1.2 MB').
    """
    if size_bytes < 0:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


# ─── SQLite helpers ────────────────────────────────────────────────────────────


def copy_db_to_temp(db_path: Path) -> Optional[Path]:
    """
    Copy a (possibly locked) SQLite database to a temporary file so we can
    read it safely while the browser is running.

    Args:
        db_path: Path to the source SQLite database.

    Returns:
        Path to the temporary copy, or None on failure.
    """
    if not db_path.exists():
        logger.debug("Database not found: %s", db_path)
        return None
    try:
        tmp_file = tempfile.NamedTemporaryFile(
            suffix=".db", prefix="browserspy_", delete=False
        )
        tmp_path = Path(tmp_file.name)
        tmp_file.close()
        shutil.copy2(db_path, tmp_path)
        logger.debug("Copied %s → %s", db_path, tmp_path)
        return tmp_path
    except PermissionError:
        logger.warning("Permission denied copying: %s", db_path)
        return None
    except Exception as exc:
        logger.debug("Failed to copy database: %s", exc)
        return None


def query_db(
    db_path: Path, query: str, params: Tuple = ()
) -> List[sqlite3.Row]:
    """
    Execute a SELECT query against an SQLite database and return all rows.

    Automatically handles locked files by working on a temporary copy.

    Args:
        db_path: Path to the SQLite database file.
        query: SQL SELECT statement.
        params: Optional tuple of query parameters.

    Returns:
        List of sqlite3.Row objects, or an empty list on failure.
    """
    tmp_path: Optional[Path] = None
    try:
        tmp_path = copy_db_to_temp(db_path)
        if tmp_path is None:
            return []

        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    except sqlite3.DatabaseError as exc:
        logger.debug("SQLite error on %s: %s", db_path, exc)
        return []
    except Exception as exc:
        logger.debug("Unexpected DB error on %s: %s", db_path, exc)
        return []
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


# ─── Abstract base parser ─────────────────────────────────────────────────────


class BaseBrowserParser(abc.ABC):
    """
    Abstract base class for all browser profile parsers.

    Subclasses implement profile discovery and artifact extraction
    for specific browsers.
    """

    BROWSER_NAME: str = "Unknown"

    def __init__(self, profile_path: Optional[Path] = None, verbose: bool = False) -> None:
        """
        Initialize the parser with an optional explicit profile path.

        Args:
            profile_path: Override path to the browser profile directory.
            verbose: Enable verbose debug logging.
        """
        self.verbose = verbose
        self._explicit_profile = profile_path
        self.profiles: List[Path] = []
        self._discover_profiles()

    def _discover_profiles(self) -> None:
        """Discover all available browser profiles for this browser."""
        if self._explicit_profile:
            if self._explicit_profile.exists():
                self.profiles = [self._explicit_profile]
            else:
                logger.warning("Provided profile path does not exist: %s", self._explicit_profile)
        else:
            self.profiles = self.find_profiles()

        if not self.profiles:
            logger.info("No profiles found for %s.", self.BROWSER_NAME)

    @abc.abstractmethod
    def find_profiles(self) -> List[Path]:
        """
        Find and return all profile directories for this browser.

        Returns:
            List of profile directory Paths.
        """
        ...

    @abc.abstractmethod
    def get_history_db(self, profile: Path) -> Optional[Path]:
        """Return path to the history database for the given profile."""
        ...

    @abc.abstractmethod
    def get_login_db(self, profile: Path) -> Optional[Path]:
        """Return path to the login/passwords database for the given profile."""
        ...

    @abc.abstractmethod
    def get_cookies_db(self, profile: Path) -> Optional[Path]:
        """Return path to the cookies database for the given profile."""
        ...

    @abc.abstractmethod
    def get_bookmarks_file(self, profile: Path) -> Optional[Path]:
        """Return path to the bookmarks file for the given profile."""
        ...

    @abc.abstractmethod
    def get_extensions_dir(self, profile: Path) -> Optional[Path]:
        """Return path to the extensions directory for the given profile."""
        ...
