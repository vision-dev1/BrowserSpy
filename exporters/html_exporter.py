# Codes By Visionnn

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BrowserSpy Report</title>
  <style>
    :root {{
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #21262d;
      --border: #30363d;
      --text: #c9d1d9;
      --muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --yellow: #d29922;
      --red: #f85149;
      --red-bg: #3d1c1c;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 24px 40px;
    }}
    header pre {{
      color: #58a6ff;
      font-size: 0.45rem;
      line-height: 1.1;
      font-family: monospace;
      white-space: pre;
    }}
    header h1 {{ color: var(--accent); font-size: 1.6rem; margin-top: 8px; }}
    header p  {{ color: var(--muted); font-size: 0.88rem; }}
    header a  {{ color: var(--accent); text-decoration: none; }}

    .dashboard {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      padding: 28px 40px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px 24px;
      min-width: 140px;
      text-align: center;
    }}
    .card .count {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
    .card .label {{ font-size: 0.8rem; color: var(--muted); margin-top: 4px; }}

    main {{ padding: 0 40px 60px; }}

    details {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 16px;
    }}
    summary {{
      padding: 14px 20px;
      cursor: pointer;
      font-size: 1rem;
      font-weight: 600;
      color: var(--accent);
      list-style: none;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    summary::-webkit-details-marker {{ display: none; }}
    summary::before {{ content: '\u25B6'; font-size: 0.7rem; transition: transform .2s; }}
    details[open] summary::before {{ transform: rotate(90deg); }}

    .table-wrap {{ overflow-x: auto; padding: 0 8px 12px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }}
    th {{
      background: var(--surface2);
      color: var(--muted);
      text-align: left;
      padding: 8px 12px;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    td {{
      padding: 7px 12px;
      border-bottom: 1px solid var(--border);
      word-break: break-all;
      max-width: 300px;
    }}
    tr:hover td {{ background: var(--surface2); }}
    .flag-red   {{ background: var(--red-bg); color: var(--red); }}
    .flag-yellow {{ background: #2d2a1a; color: var(--yellow); }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: 600;
    }}
    .badge-red    {{ background: var(--red-bg); color: var(--red); }}
    .badge-yellow {{ background: #2d2a1a; color: var(--yellow); }}
    .badge-green  {{ background: #1a2d1a; color: var(--green); }}

    footer {{
      text-align: center;
      padding: 20px;
      color: var(--muted);
      font-size: 0.8rem;
      border-top: 1px solid var(--border);
    }}
    footer a {{ color: var(--accent); text-decoration: none; }}
    .empty {{ color: var(--muted); padding: 12px 20px; font-style: italic; }}
  </style>
</head>
<body>

<header>
  <pre>\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557    \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557   \u2588\u2588\u2557
\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551    \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255D\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255D\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255D\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u255A\u2588\u2588\u2557 \u2588\u2588\u2554\u255D
\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551 \u2588\u2557 \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D \u255A\u2588\u2588\u2588\u2588\u2554\u255D
\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2557\u2588\u2588\u2551\u255A\u2550\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u255D  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u255A\u2550\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u255D   \u255A\u2588\u2554\u255D
\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D\u2588\u2588\u2551  \u2588\u2588\u2551\u255A\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255D\u255A\u2588\u2588\u2588\u2554\u2588\u2588\u2588\u2554\u255D\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551        \u2588\u2588\u2551
\u255A\u2550\u2550\u2550\u2550\u2550\u255D \u255A\u2550\u255D  \u255A\u2550\u255D \u255A\u2550\u2550\u2550\u2550\u2550\u255D  \u255A\u2550\u2550\u255D\u255A\u2550\u2550\u255D \u255A\u2550\u2550\u2550\u2550\u2550\u2550\u255D\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u255D\u255A\u2550\u255D  \u255A\u2550\u255D\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u255D\u255A\u2550\u255D        \u255A\u2550\u255D</pre>
  <h1>BrowserSpy Forensic Report</h1>
  <p>
    <strong>Generated:</strong> {generated_at} &nbsp;|&nbsp;
    Version: 1.0.0 &nbsp;|&nbsp;
    Author: <a href="https://github.com/vision-dev1" target="_blank">vision-dev1</a> &nbsp;|&nbsp;
    <a href="https://visionkc.com.np" target="_blank">visionkc.com.np</a>
  </p>
</header>

<div class="dashboard">
  {dashboard_cards}
</div>

<main>
  {sections}
</main>

<footer>
  Generated by <a href="https://github.com/vision-dev1/BrowserSpy">BrowserSpy</a> v1.0.0 &mdash;
  For educational and forensic use only.
  &nbsp;|&nbsp; <a href="https://visionkc.com.np">visionkc.com.np</a>
</footer>

</body>
</html>
"""


def _card(icon: str, label: str, count: int) -> str:
    """Generate a dashboard summary card HTML snippet."""
    return f"""
    <div class="card">
      <div class="count">{count}</div>
      <div class="label">{icon} {label}</div>
    </div>"""


def _make_table(records: List[dict], suspicious_key: str = "suspicious") -> str:
    """
    Generate an HTML table from a list of dictionaries.

    Args:
        records: List of dicts (all with same keys).
        suspicious_key: Key name in record dict that marks suspicious rows.

    Returns:
        HTML string of a <table> element, or empty message.
    """
    if not records:
        return '<p class="empty">No data collected.</p>'

    headers = list(records[0].keys())
    rows_html = ""
    for rec in records:
        is_sus = rec.get(suspicious_key, False)
        row_class = "flag-red" if is_sus else ""
        cells = ""
        for h in headers:
            val = rec.get(h, "")
            if isinstance(val, bool):
                badge_cls = "badge-green" if val else ""
                val = f'<span class="badge {badge_cls}">{"✔" if val else "✗"}</span>'
            elif isinstance(val, list):
                val = ", ".join(str(v) for v in val) if val else "—"
            else:
                val = str(val) if val else "—"
            cells += f"<td>{val}</td>"
        rows_html += f'<tr class="{row_class}">{cells}</tr>'

    header_html = "".join(f"<th>{h.replace('_',' ').title()}</th>" for h in headers)
    return (
        f'<div class="table-wrap"><table>'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table></div>"
    )


def _section(icon: str, title: str, records: List[dict], suspicious_key: str = "suspicious") -> str:
    """Generate a collapsible <details> section with a data table."""
    table = _make_table(records, suspicious_key)
    badge = f'<span class="badge badge-{"red" if any(r.get(suspicious_key) for r in records) else "green"}">{len(records)}</span>' if records else ""
    return f"""
  <details>
    <summary>{icon} {title} {badge}</summary>
    {table}
  </details>"""


def _serialize(items: List[Any]) -> List[dict]:
    """Serialize a list of entry objects to plain dicts."""
    return [item.to_dict() if hasattr(item, "to_dict") else item for item in (items or [])]


def export_html(data: Any, output_file: str, generated_at: str = "N/A") -> None:
    """
    Generate and write a dark-themed HTML report.

    Args:
        data: List of per-browser data dicts (from build_export_dict), or a single dict.
        output_file: Destination filename (e.g. 'report.html').
        generated_at: Human-readable timestamp string.
    """
    browser_records = data if isinstance(data, list) else [data]

    # Aggregate artifacts across all browsers
    history_all, downloads_all, passwords_all, cookies_all = [], [], [], []
    autofill_all, extensions_all, bookmarks_all, searches_all = [], [], [], []

    for br in browser_records:
        history_all.extend(_serialize(br.get("history", [])))
        downloads_all.extend(_serialize(br.get("downloads", [])))
        passwords_all.extend(_serialize(br.get("passwords", [])))
        cookies_all.extend(_serialize(br.get("cookies", [])))
        autofill_all.extend(_serialize(br.get("autofill", [])))
        extensions_all.extend(_serialize(br.get("extensions", [])))
        bookmarks_all.extend(_serialize(br.get("bookmarks", [])))
        searches_all.extend(_serialize(br.get("searches", [])))

    dashboard_cards = (
        _card("🕒", "History", len(history_all))
        + _card("⬇", "Downloads", len(downloads_all))
        + _card("🔑", "Passwords", len(passwords_all))
        + _card("🍪", "Cookies", len(cookies_all))
        + _card("📝", "Autofill", len(autofill_all))
        + _card("🧩", "Extensions", len(extensions_all))
        + _card("🔖", "Bookmarks", len(bookmarks_all))
        + _card("🔍", "Searches", len(searches_all))
    )

    sections = (
        _section("🕒", "Browsing History", history_all)
        + _section("⬇", "Download History", downloads_all)
        + _section("🔑", "Saved Passwords", passwords_all, "suspicious")
        + _section("🍪", "Cookies", cookies_all, "high_value")
        + _section("📝", "Autofill / Form Data", autofill_all)
        + _section("🧩", "Extensions / Addons", extensions_all)
        + _section("🔖", "Bookmarks", bookmarks_all)
        + _section("🔍", "Search Queries", searches_all)
    )

    html = HTML_TEMPLATE.format(
        generated_at=generated_at,
        dashboard_cards=dashboard_cards,
        sections=sections,
    )

    output_path = Path(output_file)
    try:
        output_path.write_text(html, encoding="utf-8")
        from utils.colors import success
        success(f"HTML report saved → {output_path.resolve()}")
    except OSError as exc:
        from utils.colors import error
        error(f"Could not write HTML report: {exc}")
