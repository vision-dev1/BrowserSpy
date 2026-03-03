"""
BrowserSpy — Firefox parser.
Handles profile discovery for Mozilla Firefox across Windows, Linux, macOS.
"""

import configparser
import logging
import sys
from pathlib import Path
from typing import List, Optional

from parsers.base import BaseBrowserParser

logger = logging.getLogger(__name__)

_PLATFORM: str = sys.platform


def _get_firefox_root() -> List[Path]:
    """
    Return candidate Firefox profile root directories for the current platform.

    Returns:
        List of candidate Path objects.
    """
    if _PLATFORM.startswith("linux"):
        return [
            Path.home() / ".mozilla" / "firefox",
        ]
    elif _PLATFORM == "darwin":
        return [
            Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles",
        ]
    elif _PLATFORM == "win32":
        return [
            Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles",
        ]
    return [Path.home() / ".mozilla" / "firefox"]


class FirefoxParser(BaseBrowserParser):
    """
    Parser for Mozilla Firefox.

    Reads the Firefox 'profiles.ini' to discover profiles, and provides
    paths to all relevant SQLite databases and data files.
    """

    BROWSER_NAME = "Firefox"

    def __init__(
        self, profile_path: Optional[Path] = None, verbose: bool = False
    ) -> None:
        """
        Initialize the Firefox parser.

        Args:
            profile_path: Explicit override for a Firefox profile directory.
            verbose: Enable verbose debug logging.
        """
        super().__init__(profile_path=profile_path, verbose=verbose)

    # ── Profile discovery ──────────────────────────────────────────────────────

    def find_profiles(self) -> List[Path]:
        """
        Discover Firefox profile directories via profiles.ini.

        Returns:
            List of profile directory paths.
        """
        profiles: List[Path] = []
        for firefox_root in _get_firefox_root():
            if not firefox_root.exists():
                logger.debug("Firefox root not found: %s", firefox_root)
                continue

            # Parse profiles.ini if present
            profiles_ini = firefox_root / "profiles.ini"
            if profiles_ini.exists():
                discovered = self._parse_profiles_ini(profiles_ini, firefox_root)
                profiles.extend(discovered)
            else:
                # Fallback: look for dirs containing places.sqlite
                for entry in firefox_root.iterdir():
                    if entry.is_dir() and (entry / "places.sqlite").exists():
                        profiles.append(entry)
                        logger.debug("Found Firefox profile (fallback): %s", entry)

        return profiles

    def _parse_profiles_ini(self, ini_path: Path, root: Path) -> List[Path]:
        """
        Parse a Firefox profiles.ini file and return all valid profile directories.

        Args:
            ini_path: Path to the profiles.ini file.
            root: Firefox root directory for resolving relative paths.

        Returns:
            List of validated profile directory paths.
        """
        config = configparser.ConfigParser()
        try:
            config.read(str(ini_path), encoding="utf-8")
        except Exception as exc:
            logger.debug("Failed to parse profiles.ini: %s", exc)
            return []

        profiles: List[Path] = []
        for section in config.sections():
            if not section.startswith("Profile"):
                continue
            if not config.has_option(section, "Path"):
                continue

            rel_path = config.get(section, "Path")
            is_relative = config.get(section, "IsRelative", fallback="1") == "1"

            if is_relative:
                profile_dir = root / rel_path
            else:
                profile_dir = Path(rel_path)

            if profile_dir.exists():
                profiles.append(profile_dir)
                logger.debug("Found Firefox profile: %s", profile_dir)

        return profiles

    # ── Database paths ─────────────────────────────────────────────────────────

    def get_history_db(self, profile: Path) -> Optional[Path]:
        """Return the path to places.sqlite (history + bookmarks)."""
        p = profile / "places.sqlite"
        return p if p.exists() else None

    def get_login_db(self, profile: Path) -> Optional[Path]:
        """Return the path to logins.json (saved passwords)."""
        p = profile / "logins.json"
        return p if p.exists() else None

    def get_key_db(self, profile: Path) -> Optional[Path]:
        """Return the path to key4.db (Firefox password encryption key database)."""
        p = profile / "key4.db"
        return p if p.exists() else None

    def get_cookies_db(self, profile: Path) -> Optional[Path]:
        """Return the path to cookies.sqlite."""
        p = profile / "cookies.sqlite"
        return p if p.exists() else None

    def get_form_history_db(self, profile: Path) -> Optional[Path]:
        """Return the path to formhistory.sqlite (autofill data)."""
        p = profile / "formhistory.sqlite"
        return p if p.exists() else None

    def get_bookmarks_file(self, profile: Path) -> Optional[Path]:
        """
        Firefox stores bookmarks in places.sqlite, not a separate file.
        Returns places.sqlite as the bookmark source.
        """
        return self.get_history_db(profile)

    def get_extensions_dir(self, profile: Path) -> Optional[Path]:
        """Return the path to the extensions directory."""
        p = profile / "extensions"
        return p if p.exists() else None

    def get_extensions_json(self, profile: Path) -> Optional[Path]:
        """Return the path to extensions.json (more complete metadata)."""
        p = profile / "extensions.json"
        return p if p.exists() else None

    def get_downloads_db(self, profile: Path) -> Optional[Path]:
        """Firefox 3.0+ stores downloads in places.sqlite; return it."""
        return self.get_history_db(profile)
