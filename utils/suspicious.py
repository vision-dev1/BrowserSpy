"""
BrowserSpy — Suspicious item detection helpers.
Defines rules for flagging potentially dangerous files, domains, extensions,
and permissions.
"""

from pathlib import Path
from typing import List, Set

# ─── Suspicious file extensions ───────────────────────────────────────────────

SUSPICIOUS_EXTENSIONS: Set[str] = {
    ".exe",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".jse",
    ".wsh",
    ".wsf",
    ".hta",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".dmg",
    ".pkg",
    ".deb",
    ".rpm",
    ".msi",
    ".dll",
    ".so",
    ".dylib",
    ".apk",
    ".ipa",
    ".scr",
    ".pif",
    ".com",
    ".lnk",
    ".jar",
    ".class",
    ".py",
    ".rb",
    ".pl",
    ".php",
    ".asp",
    ".aspx",
}

# ─── High-value cookie domains ─────────────────────────────────────────────────

HIGH_VALUE_DOMAINS: List[str] = [
    "google.com",
    "accounts.google.com",
    "facebook.com",
    "github.com",
    "paypal.com",
    "amazon.com",
    "apple.com",
    "microsoft.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "bank",
    "banking",
    "crypto",
    "coinbase.com",
    "binance.com",
    "stripe.com",
    "dropbox.com",
    "icloud.com",
    "outlook.com",
    "yahoo.com",
    "chase.com",
    "wellsfargo.com",
    "citi.com",
    "netflix.com",
    "steam",
    "reddit.com",
    "instagram.com",
    "discord.com",
    "slack.com",
    "zoom.us",
    "aws.amazon.com",
]

# ─── Dangerous extension permissions ──────────────────────────────────────────

DANGEROUS_PERMISSIONS: Set[str] = {
    "<all_urls>",
    "http://*/*",
    "https://*/*",
    "*://*/*",
    "webRequest",
    "webRequestBlocking",
    "nativeMessaging",
    "debugger",
    "management",
    "privacy",
    "proxy",
    "cookies",
    "downloads",
    "history",
    "bookmarks",
    "clipboardRead",
    "clipboardWrite",
    "contentSettings",
    "declarativeNetRequest",
    "declarativeNetRequestFeedback",
    "desktopCapture",
    "displaySource",
    "tabCapture",
    "pageCapture",
    "identity",
    "signedInDevices",
    "vpnProvider",
}

# ─── Known malicious or adware extension IDs ──────────────────────────────────

KNOWN_SUSPICIOUS_EXTENSION_IDS: Set[str] = {
    "aapocclcgogkmnckokdopfmhonfmgoek",  # example placeholder
}


def is_suspicious_file(filename: str) -> bool:
    """
    Check whether a filename has a potentially dangerous extension.

    Args:
        filename: Filename or path string to evaluate.

    Returns:
        True if the file extension is in the suspicious list.
    """
    suffix = Path(filename).suffix.lower()
    return suffix in SUSPICIOUS_EXTENSIONS


def is_high_value_domain(domain: str) -> bool:
    """
    Check whether a domain is considered high-value (frequently targeted by attacks).

    Args:
        domain: Domain name string (e.g., 'google.com').

    Returns:
        True if the domain matches any high-value domain pattern.
    """
    domain_lower = domain.lower().strip(".")
    for hvd in HIGH_VALUE_DOMAINS:
        if hvd in domain_lower:
            return True
    return False


def has_dangerous_permissions(permissions: List[str]) -> List[str]:
    """
    Return a list of dangerous permissions found in the provided permissions list.

    Args:
        permissions: List of permission strings from an extension manifest.

    Returns:
        List of permissions that match the dangerous permission set.
    """
    return [p for p in permissions if p in DANGEROUS_PERMISSIONS]


def is_session_cookie(name: str, value: str) -> bool:
    """
    Heuristically determine whether a cookie is a session/authentication token.

    Args:
        name: Cookie name.
        value: Cookie value.

    Returns:
        True if the cookie appears to be a session or auth token.
    """
    session_keywords = {
        "session",
        "sess",
        "token",
        "auth",
        "sid",
        "csrf",
        "jwt",
        "bearer",
        "access_token",
        "refresh_token",
        "oauth",
        "remember_me",
        "user_id",
        "uid",
    }
    name_lower = name.lower()
    return any(kw in name_lower for kw in session_keywords)


def flag_suspicious_url(url: str) -> bool:
    """
    Check whether a URL contains patterns commonly associated with phishing or malware.

    Args:
        url: URL string to evaluate.

    Returns:
        True if the URL looks suspicious.
    """
    lowered = url.lower()
    suspicious_patterns = [
        "login-secure",
        "account-verify",
        "verify-account",
        "update-billing",
        "confirm-identity",
        ".ru/",
        ".cn/",
        "bit.ly",
        "tinyurl",
        "goo.gl",
        "ow.ly",
        "t.co",
        "phish",
        "malware",
        "ransomware",
    ]
    return any(p in lowered for p in suspicious_patterns)
