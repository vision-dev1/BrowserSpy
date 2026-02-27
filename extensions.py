"""
BrowserSpy — Browser extension / addon lister.
Supports Chrome/Edge/Brave (Extensions/ directory) and Firefox (extensions.json).
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from parsers.chrome import ChromiumParser
from parsers.firefox import FirefoxParser
from utils.suspicious import has_dangerous_permissions, KNOWN_SUSPICIOUS_EXTENSION_IDS

logger = logging.getLogger(__name__)


@dataclass
class ExtensionEntry:
    """Represents a browser extension or addon."""

    browser: str
    profile: str
    ext_id: str
    name: str
    version: str
    description: str
    permissions: List[str] = field(default_factory=list)
    dangerous_permissions: List[str] = field(default_factory=list)
    suspicious: bool = False

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "browser": self.browser,
            "profile": self.profile,
            "ext_id": self.ext_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "permissions": self.permissions,
            "dangerous_permissions": self.dangerous_permissions,
            "suspicious": self.suspicious,
        }


# ─── Chrome/Edge/Brave ────────────────────────────────────────────────────────


def _read_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read and parse a Chrome extension manifest.json file.

    Args:
        manifest_path: Path to manifest.json.

    Returns:
        Parsed manifest dict, or None on failure.
    """
    try:
        with open(manifest_path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception as exc:
        logger.debug("Failed to read manifest %s: %s", manifest_path, exc)
        return None


def extract_chromium_extensions(
    parser: ChromiumParser, limit: Optional[int] = None
) -> List[ExtensionEntry]:
    """
    List all installed extensions in Chromium-based browser profiles.

    Reads each extension's manifest.json from the Extensions/ directory.

    Args:
        parser: Initialized ChromiumParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of ExtensionEntry objects.
    """
    results: List[ExtensionEntry] = []

    for profile in parser.profiles:
        ext_dir = parser.get_extensions_dir(profile)
        if ext_dir is None:
            continue

        for ext_id_dir in sorted(ext_dir.iterdir()):
            if not ext_id_dir.is_dir():
                continue
            ext_id = ext_id_dir.name

            # Each extension may have multiple version sub-directories
            manifests = list(ext_id_dir.glob("*/manifest.json"))
            if not manifests:
                manifests = list(ext_id_dir.glob("manifest.json"))

            manifest = None
            for m_path in sorted(manifests, reverse=True):
                manifest = _read_manifest(m_path)
                if manifest:
                    break

            if manifest is None:
                continue

            name = manifest.get("name", ext_id)
            # Handle __MSG_* locale keys
            if name.startswith("__MSG_"):
                name = f"[localized: {ext_id}]"

            permissions: List[str] = manifest.get("permissions", []) + manifest.get(
                "host_permissions", []
            )
            dangerous = has_dangerous_permissions(permissions)
            is_suspicious = bool(dangerous) or (ext_id in KNOWN_SUSPICIOUS_EXTENSION_IDS)

            entry = ExtensionEntry(
                browser=parser.BROWSER_NAME,
                profile=profile.name,
                ext_id=ext_id,
                name=name,
                version=manifest.get("version", "?"),
                description=manifest.get("description", "")[:120],
                permissions=permissions,
                dangerous_permissions=dangerous,
                suspicious=is_suspicious,
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Firefox ──────────────────────────────────────────────────────────────────


def extract_firefox_extensions(
    parser: FirefoxParser, limit: Optional[int] = None
) -> List[ExtensionEntry]:
    """
    List all installed extensions in Firefox profiles via extensions.json.

    Args:
        parser: Initialized FirefoxParser instance.
        limit: Maximum number of entries per profile.

    Returns:
        List of ExtensionEntry objects.
    """
    results: List[ExtensionEntry] = []

    for profile in parser.profiles:
        ext_json_path = parser.get_extensions_json(profile)
        if ext_json_path is None:
            logger.debug("No extensions.json in profile: %s", profile)
            continue

        try:
            with open(ext_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.warning("Cannot read extensions.json: %s", exc)
            continue

        addons = data.get("addons", [])
        for addon in addons:
            if addon.get("type") not in ("extension", None):
                continue

            ext_id = addon.get("id", "?")
            permissions: List[str] = addon.get("userPermissions", {}).get("permissions", []) + \
                addon.get("userPermissions", {}).get("origins", [])
            dangerous = has_dangerous_permissions(permissions)
            is_suspicious = bool(dangerous)

            entry = ExtensionEntry(
                browser="Firefox",
                profile=profile.name,
                ext_id=ext_id,
                name=addon.get("defaultLocale", {}).get("name", ext_id),
                version=addon.get("version", "?"),
                description=addon.get("defaultLocale", {}).get("description", "")[:120],
                permissions=permissions,
                dangerous_permissions=dangerous,
                suspicious=is_suspicious,
            )
            results.append(entry)

        if limit:
            results = results[:limit]

    return results


# ─── Display ──────────────────────────────────────────────────────────────────


def display_extensions(entries: List[ExtensionEntry], suspicious_only: bool = False) -> None:
    """
    Display extensions in a rich terminal table.

    Args:
        entries: List of ExtensionEntry objects.
        suspicious_only: If True, only show flagged (dangerous) extensions.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    filtered = [e for e in entries if e.suspicious] if suspicious_only else entries

    if not filtered:
        console.print("[yellow][!] No extensions to display.[/yellow]")
        return

    table = Table(
        title=f"🧩 Browser Extensions ({len(filtered)} entries)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Browser", style="cyan", no_wrap=True)
    table.add_column("Name", style="white", max_width=30)
    table.add_column("Version", style="blue")
    table.add_column("ID", style="dim", max_width=34)
    table.add_column("Dangerous Perms", style="red", max_width=40)
    table.add_column("⚠", justify="center")

    for e in filtered:
        flag = "🔴" if e.suspicious else ""
        style = "bold red" if e.suspicious else ""
        perms_str = ", ".join(e.dangerous_permissions) if e.dangerous_permissions else "—"
        table.add_row(
            e.browser, e.name, e.version, e.ext_id, perms_str, flag, style=style
        )

    console.print(table)
