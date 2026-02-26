
"""
BrowserSpy — Main entry point.

CLI tool for extracting and analyzing browser forensic artifacts:
history, downloads, passwords, cookies, autofill, extensions, bookmarks,
and search queries from Chrome, Firefox, Edge, and Brave.

Usage:
    python browserspy.py --help
    python browserspy.py --browser chrome --all
    python browserspy.py --browser firefox --history --limit 50
    python browserspy.py --browser all --all --output html --file report.html

Author: vision-dev1
GitHub: https://github.com/vision-dev1
Portfolio: https://visionkc.com.np
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Internal imports ─────────────────────────────────────────────────────────

from utils.banner import print_banner
from utils.colors import console, error, info, success, verbose_log, warning

# ─── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("browserspy")


# ─── Parser factory ────────────────────────────────────────────────────────────


def _make_parsers(browser_arg: str, verbose: bool) -> List[Any]:
    """
    Instantiate and return parser objects for the requested browser(s).

    Args:
        browser_arg: One of 'chrome', 'firefox', 'edge', 'brave', 'all'.
        verbose:     Enable verbose debug logging.

    Returns:
        List of parser instances (ChromiumParser or FirefoxParser).
    """
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser

    parsers = []
    browsers = (
        ["chrome", "firefox", "edge", "brave"]
        if browser_arg == "all"
        else [browser_arg]
    )

    for b in browsers:
        if b == "firefox":
            p = FirefoxParser(verbose=verbose)
        else:
            try:
                p = ChromiumParser(browser=b, verbose=verbose)
            except ValueError as exc:
                error(str(exc))
                continue

        if not p.profiles:
            warning(f"No {b.capitalize()} profiles found on this system — skipping.")
            continue

        info(f"Found {len(p.profiles)} {b.capitalize()} profile(s).")
        parsers.append(p)

    return parsers


# ─── Module runners ────────────────────────────────────────────────────────────


def _run_history(parsers: List[Any], limit: Optional[int], suspicious_only: bool) -> List[Any]:
    """Run history extraction across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.history import (
        extract_chromium_history,
        extract_firefox_history,
        display_history,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_history(p, limit=limit)
        else:
            entries = extract_firefox_history(p, limit=limit)
        all_entries.extend(entries)

    display_history(all_entries, suspicious_only=suspicious_only)
    return all_entries


def _run_downloads(parsers: List[Any], limit: Optional[int], suspicious_only: bool) -> List[Any]:
    """Run download history extraction across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.downloads import (
        extract_chromium_downloads,
        extract_firefox_downloads,
        display_downloads,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_downloads(p, limit=limit)
        else:
            entries = extract_firefox_downloads(p, limit=limit)
        all_entries.extend(entries)

    display_downloads(all_entries, suspicious_only=suspicious_only)
    return all_entries


def _run_passwords(parsers: List[Any], limit: Optional[int]) -> List[Any]:
    """Run password extraction across all parsers (with user confirmation)."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.passwords import (
        extract_chromium_passwords,
        extract_firefox_passwords,
        display_passwords,
    )

    console.print(
        "\n[bold yellow][!] You are about to extract saved passwords.[/bold yellow]"
    )
    confirm = console.input("[bold]Continue? (yes/no): [/bold]").strip().lower()
    if confirm not in ("yes", "y"):
        warning("Password extraction cancelled.")
        return []

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_passwords(p, limit=limit)
        else:
            entries = extract_firefox_passwords(p, limit=limit)
        all_entries.extend(entries)

    display_passwords(all_entries)
    return all_entries


def _run_cookies(parsers: List[Any], limit: Optional[int], suspicious_only: bool) -> List[Any]:
    """Run cookie extraction across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.cookies import (
        extract_chromium_cookies,
        extract_firefox_cookies,
        display_cookies,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_cookies(p, limit=limit)
        else:
            entries = extract_firefox_cookies(p, limit=limit)
        all_entries.extend(entries)

    display_cookies(all_entries, suspicious_only=suspicious_only)
    return all_entries


def _run_autofill(parsers: List[Any], limit: Optional[int]) -> List[Any]:
    """Run autofill extraction across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.autofill import (
        extract_chromium_autofill,
        extract_firefox_autofill,
        display_autofill,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_autofill(p, limit=limit)
        else:
            entries = extract_firefox_autofill(p, limit=limit)
        all_entries.extend(entries)

    display_autofill(all_entries)
    return all_entries


def _run_extensions(parsers: List[Any], limit: Optional[int], suspicious_only: bool) -> List[Any]:
    """Run extension listing across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.extensions import (
        extract_chromium_extensions,
        extract_firefox_extensions,
        display_extensions,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_extensions(p, limit=limit)
        else:
            entries = extract_firefox_extensions(p, limit=limit)
        all_entries.extend(entries)

    display_extensions(all_entries, suspicious_only=suspicious_only)
    return all_entries


def _run_bookmarks(parsers: List[Any], limit: Optional[int]) -> List[Any]:
    """Run bookmark extraction across all parsers."""
    from parsers.chrome import ChromiumParser
    from parsers.firefox import FirefoxParser
    from modules.bookmarks import (
        extract_chromium_bookmarks,
        extract_firefox_bookmarks,
        display_bookmarks,
    )

    all_entries = []
    for p in parsers:
        if isinstance(p, ChromiumParser):
            entries = extract_chromium_bookmarks(p, limit=limit)
        else:
            entries = extract_firefox_bookmarks(p, limit=limit)
        all_entries.extend(entries)

    display_bookmarks(all_entries)
    return all_entries


def _run_searches(history_entries: List[Any], limit: Optional[int]) -> List[Any]:
    """Extract search queries from already-fetched history entries."""
    from modules.searches import extract_searches_from_history, display_searches

    searches = extract_searches_from_history(history_entries, limit=limit)
    display_searches(searches)
    return searches


# ─── Export dispatcher ─────────────────────────────────────────────────────────


def _export(
    output_fmt: str,
    output_file: Optional[str],
    browser_data: List[Dict[str, Any]],
    generated_at: str,
) -> None:
    """
    Export collected data in the requested format.

    Args:
        output_fmt: 'json', 'html', 'csv', or 'txt'.
        output_file: Destination filename.
        browser_data: List of per-browser data dicts.
        generated_at: ISO timestamp string for report metadata.
    """
    if output_fmt == "json":
        from exporters.json_exporter import export_json
        payload = {"metadata": {"generated_at": generated_at, "tool": "BrowserSpy v1.0.0"}, "data": browser_data}
        export_json(payload, output_file or "browserspy_report.json")

    elif output_fmt == "html":
        from exporters.html_exporter import export_html
        export_html(browser_data, output_file or "browserspy_report.html", generated_at=generated_at)

    elif output_fmt == "csv":
        from exporters.csv_exporter import export_csv
        prefix = Path(output_file).stem if output_file else "browserspy"
        export_csv(browser_data, output_prefix=prefix)

    elif output_fmt == "txt":
        info("TXT output is displayed in the terminal (default mode). No file export needed.")

    else:
        warning(f"Unknown output format: {output_fmt!r}. No export performed.")


# ─── CLI argument parsing ──────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse CLI argument parser."""
    ap = argparse.ArgumentParser(
        prog="browserspy",
        description=(
            "BrowserSpy — Spy on your browser before someone else does.\n"
            "Extract history, passwords, cookies, extensions, and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python browserspy.py --browser chrome --all\n"
            "  python browserspy.py --browser firefox --history --limit 100\n"
            "  python browserspy.py --browser all --cookies --suspicious\n"
            "  python browserspy.py --browser chrome --all --output html --file report.html\n"
        ),
    )

    ap.add_argument(
        "--browser",
        choices=["chrome", "firefox", "edge", "brave", "all"],
        default="all",
        help="Target browser to analyze (default: all).",
    )

    # ── Artifact flags ────────────────────────────────────────────────────────
    artifacts = ap.add_argument_group("artifact selection")
    artifacts.add_argument("--history",     action="store_true", help="Extract browsing history.")
    artifacts.add_argument("--downloads",   action="store_true", help="Extract download history.")
    artifacts.add_argument("--passwords",   action="store_true", help="Extract saved passwords.")
    artifacts.add_argument("--cookies",     action="store_true", help="Extract cookies.")
    artifacts.add_argument("--autofill",    action="store_true", help="Extract autofill/form data.")
    artifacts.add_argument("--extensions",  action="store_true", help="List installed extensions.")
    artifacts.add_argument("--bookmarks",   action="store_true", help="Extract bookmarks.")
    artifacts.add_argument("--searches",    action="store_true", help="Extract search queries.")
    artifacts.add_argument("--all",         action="store_true", help="Run all extraction modules.")

    # ── Output flags ──────────────────────────────────────────────────────────
    output_grp = ap.add_argument_group("output")
    output_grp.add_argument(
        "--output",
        choices=["json", "html", "csv", "txt"],
        default="txt",
        help="Output format (default: txt — terminal display).",
    )
    output_grp.add_argument("--file", metavar="FILENAME", help="Output filename.")
    output_grp.add_argument("--limit", type=int, metavar="N", help="Limit results to N entries.")
    output_grp.add_argument("--suspicious", action="store_true", help="Show only suspicious/flagged items.")
    output_grp.add_argument("--verbose",    action="store_true", help="Enable verbose debug logging.")
    output_grp.add_argument("--no-banner",  action="store_true", help="Suppress the banner.")

    return ap


# ─── Main orchestration ────────────────────────────────────────────────────────


def main() -> None:
    """
    BrowserSpy main function.
    Parses CLI arguments, discovers browser profiles, runs selected extraction
    modules, and exports results in the requested format.
    """
    ap = build_parser()
    args = ap.parse_args()

    # ── Banner ────────────────────────────────────────────────────────────────
    print_banner(no_banner=args.no_banner)

    # ── Verbose mode ──────────────────────────────────────────────────────────
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

    # ── Validate at least one action selected ─────────────────────────────────
    any_artifact = any([
        args.history, args.downloads, args.passwords, args.cookies,
        args.autofill, args.extensions, args.bookmarks, args.searches, args.all,
    ])
    if not any_artifact:
        ap.print_help()
        console.print(
            "\n[yellow][!] Please specify an artifact flag (e.g. --history, --all).[/yellow]"
        )
        sys.exit(0)

    # ── Browser profile discovery ─────────────────────────────────────────────
    info(f"Targeting browser(s): [bold]{args.browser}[/bold]")
    parsers = _make_parsers(args.browser, verbose=args.verbose)
    if not parsers:
        error("No browser profiles found. Is a supported browser installed?")
        sys.exit(1)

    # ── Run requested modules ─────────────────────────────────────────────────
    from rich.progress import Progress, SpinnerColumn, TextColumn

    history_entries: List[Any] = []
    browser_data: List[Dict[str, Any]] = []

    # Collect per-browser results for export
    per_browser_results: Dict[str, Dict[str, List[Any]]] = {}

    def _result_key(p) -> str:
        return getattr(p, "browser", getattr(p, "BROWSER_NAME", "unknown"))

    for p in parsers:
        per_browser_results[_result_key(p)] = {
            "history": [], "downloads": [], "passwords": [],
            "cookies": [], "autofill": [], "extensions": [],
            "bookmarks": [], "searches": [],
        }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:

        if args.history or args.all:
            task = progress.add_task("Extracting history…", total=None)
            with progress:
                entries = _run_history(parsers, args.limit, args.suspicious)
            history_entries = entries
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["history"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.downloads or args.all:
            task = progress.add_task("Extracting downloads…", total=None)
            entries = _run_downloads(parsers, args.limit, args.suspicious)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["downloads"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.passwords or args.all:
            task = progress.add_task("Extracting passwords…", total=None)
            entries = _run_passwords(parsers, args.limit)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["passwords"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.cookies or args.all:
            task = progress.add_task("Extracting cookies…", total=None)
            entries = _run_cookies(parsers, args.limit, args.suspicious)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["cookies"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.autofill or args.all:
            task = progress.add_task("Extracting autofill…", total=None)
            entries = _run_autofill(parsers, args.limit)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["autofill"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.extensions or args.all:
            task = progress.add_task("Listing extensions…", total=None)
            entries = _run_extensions(parsers, args.limit, args.suspicious)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["extensions"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.bookmarks or args.all:
            task = progress.add_task("Extracting bookmarks…", total=None)
            entries = _run_bookmarks(parsers, args.limit)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["bookmarks"] = [e for e in entries if e.browser.lower() == key]
            progress.remove_task(task)

        if args.searches or args.all:
            task = progress.add_task("Extracting search queries…", total=None)
            if not history_entries:
                # Load history silently for search extraction
                for p in parsers:
                    from parsers.chrome import ChromiumParser
                    from parsers.firefox import FirefoxParser
                    from modules.history import extract_chromium_history, extract_firefox_history
                    if isinstance(p, ChromiumParser):
                        history_entries.extend(extract_chromium_history(p))
                    else:
                        history_entries.extend(extract_firefox_history(p))
            searches = _run_searches(history_entries, args.limit)
            for p in parsers:
                key = _result_key(p)
                per_browser_results[key]["searches"] = [e for e in searches if e.browser.lower() == key]
            progress.remove_task(task)

    # ── Export ────────────────────────────────────────────────────────────────
    if args.output != "txt" or args.file:
        from exporters.json_exporter import build_export_dict
        browser_data = [
            build_export_dict(
                browser=key,
                history=v["history"],
                downloads=v["downloads"],
                passwords=v["passwords"],
                cookies=v["cookies"],
                autofill=v["autofill"],
                extensions=v["extensions"],
                bookmarks=v["bookmarks"],
                searches=v["searches"],
            )
            for key, v in per_browser_results.items()
        ]
        _export(args.output, args.file, browser_data, generated_at)

    console.print("\n[bold green]✔ BrowserSpy scan complete.[/bold green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        error(f"Unexpected error: {exc}")
        logger.exception("Fatal error in BrowserSpy main()")
        sys.exit(1)
