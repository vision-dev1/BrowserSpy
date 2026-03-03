"""
BrowserSpy — Chrome / Edge / Brave parser.
Handles profile discovery for Chromium-based browsers across Windows, Linux, macOS.
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

from parsers.base import BaseBrowserParser

logger = logging.getLogger(__name__)

# ─── Profile path definitions ──────────────────────────────────────────────────

# Each entry: (browser_name, {platform: [candidate_dirs]})
_CHROMIUM_PROFILE_ROOTS: dict = {
    "chrome": {
        "linux": [
            Path.home() / ".config" / "google-chrome",
        ],
        "darwin": [
            Path.home() / "Library" / "Application Support" / "Google" / "Chrome",
        ],
        "win32": [
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
        ],
    },
    "edge": {
        "linux": [
            Path.home() / ".config" / "microsoft-edge",
        ],
        "darwin": [
            Path.home() / "Library" / "Application Support" / "Microsoft Edge",
        ],
        "win32": [
            Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data",
        ],
    },
    "brave": {
        "linux": [
            Path.home() / ".config" / "BraveSoftware" / "Brave-Browser",
        ],
        "darwin": [
            Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser",
        ],
        "win32": [
            Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data",
        ],
    },
}

_PLATFORM: str = sys.platform  # 'linux', 'darwin', 'win32'


def _get_platform_key() -> str:
    """Normalize sys.platform to a key in _CHROMIUM_PROFILE_ROOTS."""
    if _PLATFORM.startswith("linux"):
        return "linux"
    elif _PLATFORM == "darwin":
        return "darwin"
    elif _PLATFORM == "win32":
        return "win32"
    return "linux"  # fallback


class ChromiumParser(BaseBrowserParser):
    """
    Parser for Chromium-based browsers: Google Chrome, Microsoft Edge, Brave.

    Discovers profiles in platform-specific directories and provides
    paths to all relevant SQLite databases and data files.
    """

    def __init__(
        self,
        browser: str = "chrome",
        profile_path: Optional[Path] = None,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Chromium parser.

        Args:
            browser: Browser identifier — 'chrome', 'edge', or 'brave'.
            profile_path: Explicit override for the user data directory.
            verbose: Enable verbose debug logging.
        """
        browser = browser.lower()
        if browser not in _CHROMIUM_PROFILE_ROOTS:
            raise ValueError(f"Unsupported Chromium browser: {browser!r}")
        self.browser = browser
        self.BROWSER_NAME = browser.capitalize()
        super().__init__(profile_path=profile_path, verbose=verbose)

    # ── Profile discovery ──────────────────────────────────────────────────────

    def find_profiles(self) -> List[Path]:
        """
        Discover all Chromium profile directories for the selected browser.

        Returns:
            List of profile directory paths (e.g., Default, Profile 1, ...).
        """
        platform_key = _get_platform_key()
        candidates: List[Path] = _CHROMIUM_PROFILE_ROOTS.get(self.browser, {}).get(platform_key, [])

        profiles: List[Path] = []
        for user_data_dir in candidates:
            if not user_data_dir.exists():
                logger.debug("User data dir not found: %s", user_data_dir)
                continue

            # Look for profile sub-directories: Default, Profile 1, Profile 2, …
            for entry in user_data_dir.iterdir():
                if entry.is_dir() and (
                    entry.name == "Default" or entry.name.startswith("Profile ")
                ):
                    if (entry / "History").exists() or (entry / "Cookies").exists():
                        profiles.append(entry)
                        logger.debug("Found profile: %s", entry)

        return profiles

    def get_user_data_dir(self, profile: Path) -> Path:
        """Return the parent 'User Data' directory for a given profile."""
        return profile.parent

    # ── Database paths ─────────────────────────────────────────────────────────

    def get_history_db(self, profile: Path) -> Optional[Path]:
        """Return the path to the History SQLite database."""
        p = profile / "History"
        return p if p.exists() else None

    def get_login_db(self, profile: Path) -> Optional[Path]:
        """Return the path to the Login Data SQLite database."""
        p = profile / "Login Data"
        return p if p.exists() else None

    def get_cookies_db(self, profile: Path) -> Optional[Path]:
        """Return the path to the Cookies SQLite database."""
        # Chrome 96+ moved cookies to Network/Cookies
        network_cookies = profile / "Network" / "Cookies"
        if network_cookies.exists():
            return network_cookies
        old_cookies = profile / "Cookies"
        return old_cookies if old_cookies.exists() else None

    def get_web_data_db(self, profile: Path) -> Optional[Path]:
        """Return the path to the Web Data (autofill) SQLite database."""
        p = profile / "Web Data"
        return p if p.exists() else None

    def get_bookmarks_file(self, profile: Path) -> Optional[Path]:
        """Return the path to the Bookmarks JSON file."""
        p = profile / "Bookmarks"
        return p if p.exists() else None

    def get_extensions_dir(self, profile: Path) -> Optional[Path]:
        """Return the path to the Extensions directory."""
        p = profile / "Extensions"
        return p if p.exists() else None


# ─── Convenience factories ─────────────────────────────────────────────────────


def get_chrome_parser(profile_path: Optional[Path] = None, verbose: bool = False) -> ChromiumParser:
    """Return a ChromiumParser configured for Google Chrome."""
    return ChromiumParser(browser="chrome", profile_path=profile_path, verbose=verbose)


def get_edge_parser(profile_path: Optional[Path] = None, verbose: bool = False) -> ChromiumParser:
    """Return a ChromiumParser configured for Microsoft Edge."""
    return ChromiumParser(browser="edge", profile_path=profile_path, verbose=verbose)


def get_brave_parser(profile_path: Optional[Path] = None, verbose: bool = False) -> ChromiumParser:
    """Return a ChromiumParser configured for Brave Browser."""
    return ChromiumParser(browser="brave", profile_path=profile_path, verbose=verbose)
