<div align="center">

# BrowserSpy

 >**Spy on your browser before someone else does.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Author](https://img.shields.io/badge/Author-vision--dev1-purple)

</div>

## 📖 Overview

**BrowserSpy** is a professional, cross-platform CLI forensics tool written in Python that extracts and analyzes stored browser artifacts — including history, passwords, cookies, autofill data, extensions, bookmarks, and search queries — from all major browsers.

Built for security researchers, digital forensics analysts, and penetration testers.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🕒 **Browsing History** | URLs, titles, visit count, timestamps |
| ⬇ **Download History** | Filenames, source URLs, sizes, suspicious file flagging |
| 🔑 **Saved Passwords** | AES-GCM decryption (Chrome/Edge/Brave), NSS (Firefox) |
| 🍪 **Cookies** | Domain, value, expiry, high-value domain detection |
| 📝 **Autofill Data** | Form field values, usernames, emails |
| 🧩 **Extensions** | Name, ID, version, dangerous permission detection |
| 🔖 **Bookmarks** | Full folder hierarchy |
| 🔍 **Search Queries** | Google, Bing, DuckDuckGo, Yahoo, Yandex, Brave |

---

## 🌐 Supported Browsers

| Browser | Windows | Linux | macOS |
|---|---|---|---|
| Google Chrome | ✔ | ✔ | ✔ |
| Mozilla Firefox | ✔ | ✔ | ✔ |
| Microsoft Edge | ✔ | ✔ | ✔ |
| Brave Browser | ✔ | ✔ | ✔ |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/vision-dev1/BrowserSpy.git
cd BrowserSpy

# 2. Create and activate a virtual environment (recommended)
python3 -m venv venv

# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Optional: Windows DPAPI support
pip install pywin32

# 5. Optional: Linux Keyring support
pip install secretstorage
```

---

## 🚀 Usage

### Basic Usage
```bash
python browserspy.py --help
python browserspy.py --browser chrome --all
python browserspy.py --browser firefox --history
python browserspy.py --browser all --all
```

### Specific Artifacts
```bash
python browserspy.py --browser chrome --history --limit 50
python browserspy.py --browser chrome --passwords
python browserspy.py --browser edge --cookies
python browserspy.py --browser firefox --extensions
python browserspy.py --browser brave --bookmarks
python browserspy.py --browser chrome --searches
python browserspy.py --browser all --downloads --suspicious
```

### Export Reports
```bash
# JSON report
python browserspy.py --browser chrome --all --output json --file report.json

# HTML report (dark-themed dashboard)
python browserspy.py --browser all --all --output html --file report.html

# CSV files (one per artifact type)
python browserspy.py --browser firefox --all --output csv --file report

# Suspicious items only
python browserspy.py --browser chrome --all --suspicious
```

### All Flags
| Flag | Description |
|---|---|
| `--browser` | `chrome`, `firefox`, `edge`, `brave`, `all` |
| `--all` | Run all extraction modules |
| `--history` | Extract browsing history |
| `--downloads` | Extract download history |
| `--passwords` | Extract saved passwords |
| `--cookies` | Extract cookies |
| `--autofill` | Extract autofill / form data |
| `--extensions` | List installed extensions |
| `--bookmarks` | Extract bookmarks |
| `--searches` | Extract search queries |
| `--suspicious` | Only show suspicious / flagged items |
| `--limit N` | Limit results to N entries per module |
| `--output` | `json`, `html`, `csv`, `txt` (default: terminal) |
| `--file` | Output filename |
| `--verbose` | Enable debug logging |
| `--no-banner` | Suppress the ASCII banner |

---

## 📸 Screenshots

> _See the HTML report for a full dark-themed dashboard._

---

## 🏗 Project Structure

```
BrowserSpy/
├── browserspy.py          # Main entry point, CLI, orchestration
├── requirements.txt       # Dependencies
├── README.md
├── parsers/
│   ├── base.py            # SQLite helpers, timestamp converters, base class
│   ├── chrome.py          # Chrome / Edge / Brave profile discovery
│   └── firefox.py         # Firefox profile discovery
├── modules/
│   ├── history.py         # Browsing history extraction
│   ├── downloads.py       # Download history extraction
│   ├── passwords.py       # Password decryption
│   ├── cookies.py         # Cookie extraction
│   ├── autofill.py        # Autofill / form data
│   ├── extensions.py      # Extension / addon listing
│   ├── bookmarks.py       # Bookmark parsing
│   └── searches.py        # Search query extraction
├── exporters/
│   ├── json_exporter.py   # JSON report
│   ├── html_exporter.py   # Dark-themed HTML dashboard
│   └── csv_exporter.py    # Per-artifact CSV files
└── utils/
    ├── banner.py           # ASCII banner
    ├── colors.py           # Rich color helpers
    ├── crypto.py           # AES-GCM / DPAPI decryption
    └── suspicious.py       # Suspicious file/domain/permission detection
```

---

## 🔐 Password Decryption

| Browser | OS | Method |
|---|---|---|
| Chrome/Edge/Brave | Linux | PBKDF2 + AES-128-GCM (key from secretstorage or 'peanuts') |
| Chrome/Edge/Brave | macOS | PBKDF2 + AES-128-GCM (key from Keychain via `security` CLI) |
| Chrome/Edge/Brave | Windows | DPAPI + AES-GCM (key from Local State via pywin32) |
| Firefox | All | NSS / libnss3 decryption (best-effort; requires libnss3) |

---

## ⚠️ Legal Disclaimer

> **BrowserSpy is intended for educational and forensic purposes only.**
>
> Only use BrowserSpy on systems you own or have **explicit written permission** to analyze.
> Unauthorized access to another person's browser data is a criminal offense in most jurisdictions.
>
> The author assumes no liability for misuse of this tool.

---

## 👤 Author

**vision-dev1**

- 🐙 GitHub: [github.com/vision-dev1](https://github.com/vision-dev1)
- 🌐 Portfolio: [visionkc.com.np](https://visionkc.com.np)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
