"""Shared HTML layout — navigation bar + base styles for admin pages."""

BASE_STYLES = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }

  .navbar {
    background: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: sticky; top: 0; z-index: 10;
  }
  .navbar .brand { font-size: 1.2em; font-weight: 700; color: #38bdf8; margin-right: auto; letter-spacing: -0.5px; }
  .navbar a { color: #94a3b8; text-decoration: none; padding: 8px 14px; border-radius: 8px; font-size: 0.95em; transition: all 0.15s; }
  .navbar a:hover { color: #e2e8f0; background: #0f172a; }
  .navbar a.active { color: #38bdf8; background: #0f172a; }
  .navbar a.logout { color: #f87171; margin-left: 8px; }
  .navbar a.logout:hover { background: #450a0a; }

  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
  h1 { color: #38bdf8; margin-bottom: 8px; font-size: 1.8em; }
  h2 { color: #94a3b8; margin: 24px 0 12px 0; font-size: 1.1em; font-weight: 500; }
  .subtitle { color: #64748b; margin-bottom: 24px; }
</style>
"""


def nav_html(active: str = "") -> str:
    items = [
        ("test", "/", "Test"),
        ("history", "/history/view/all", "History"),
        ("stats", "/stats/dashboard", "Dashboard"),
    ]
    links = []
    for key, href, label in items:
        cls = " class=\"active\"" if key == active else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return f"""
<nav class="navbar">
    <div class="brand">NutriScan</div>
    {"".join(links)}
    <a href="/logout" class="logout">Logout</a>
</nav>
"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — NutriScan</title>
    {BASE_STYLES}
</head>
<body>
{nav_html(active)}
<div class="container">
{body}
</div>
</body>
</html>"""
