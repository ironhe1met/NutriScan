from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from ..auth import verify_credentials

router = APIRouter()


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login — NutriScan</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 40px;
    width: 100%;
    max-width: 380px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  }
  .brand {
    font-size: 1.8em;
    font-weight: 700;
    color: #38bdf8;
    text-align: center;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }
  .subtitle {
    text-align: center;
    color: #64748b;
    font-size: 0.9em;
    margin-bottom: 32px;
  }
  label {
    display: block;
    color: #94a3b8;
    font-size: 0.85em;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  input {
    width: 100%;
    background: #0f172a;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 12px 14px;
    border-radius: 10px;
    font-size: 1em;
    margin-bottom: 18px;
    transition: border 0.15s;
  }
  input:focus {
    outline: none;
    border-color: #38bdf8;
  }
  button {
    width: 100%;
    background: #38bdf8;
    color: #0f172a;
    border: none;
    padding: 13px;
    border-radius: 10px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    margin-top: 8px;
  }
  button:hover { background: #7dd3fc; }
  .error {
    background: #450a0a;
    color: #fca5a5;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.88em;
    margin-bottom: 18px;
    text-align: center;
  }
</style>
</head>
<body>
<form class="card" method="post" action="/login">
    <div class="brand">NutriScan</div>
    <div class="subtitle">Admin panel</div>
    {error}
    <label>Username</label>
    <input name="username" autofocus autocomplete="username" required>
    <label>Password</label>
    <input name="password" type="password" autocomplete="current-password" required>
    <button type="submit">Sign in</button>
</form>
</body>
</html>"""


@router.get("/login", response_class=HTMLResponse)
async def login_page(error: str | None = None):
    error_html = f'<div class="error">{error}</div>' if error else ""
    return LOGIN_HTML.replace("{error}", error_html)


@router.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_credentials(username, password):
        request.session["authenticated"] = True
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
