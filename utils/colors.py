"""
BrowserSpy — Color constants and styled output helpers.
Uses rich library for terminal color management.
"""

from rich.console import Console
from rich.theme import Theme
from rich.text import Text

# ─── Custom theme ─────────────────────────────────────────────────────────────

BROWSER_SPY_THEME = Theme(
    {
        "info": "bold cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold magenta",
        "muted": "dim white",
        "suspicious": "bold red on dark_red",
        "safe": "green",
        "header": "bold white on blue",
        "banner": "bold cyan",
        "url": "underline blue",
        "password": "bold red",
        "cookie_high": "bold red",
        "cookie_normal": "cyan",
        "extension_danger": "bold red",
        "extension_safe": "green",
    }
)

# ─── Shared console instance ───────────────────────────────────────────────────

console = Console(theme=BROWSER_SPY_THEME)


# ─── Helper functions ──────────────────────────────────────────────────────────


def info(message: str) -> None:
    """Print an info message in cyan."""
    console.print(f"[info][*] {message}[/info]")


def success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[success][+] {message}[/success]")


def warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[warning][!] {message}[/warning]")


def error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[error][-] {message}[/error]")


def verbose_log(message: str, verbose: bool = False) -> None:
    """
    Print a verbose debug message if verbose mode is enabled.

    Args:
        message: The message to display.
        verbose: Whether verbose mode is active.
    """
    if verbose:
        console.print(f"[muted][DEBUG] {message}[/muted]")


def suspicious_label() -> Text:
    """Return a styled 'SUSPICIOUS' label text."""
    return Text("⚠ SUSPICIOUS", style="suspicious")


def safe_label() -> Text:
    """Return a styled 'SAFE' label text."""
    return Text("✔ SAFE", style="safe")
