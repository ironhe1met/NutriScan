import secrets

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

from .config import settings


class NotAuthenticated(Exception):
    """Raised when HTML route needs redirect to login."""


def verify_credentials(username: str, password: str) -> bool:
    if not settings.admin_password:
        return True
    correct_user = secrets.compare_digest(
        username.encode(), settings.admin_username.encode()
    )
    correct_pass = secrets.compare_digest(
        password.encode(), settings.admin_password.get_secret_value().encode()
    )
    return correct_user and correct_pass


def is_authenticated(request: Request) -> bool:
    if not settings.admin_password:
        return True  # no password = open
    return request.session.get("authenticated", False)


async def require_admin(request: Request):
    """Dependency: HTML → redirect to /login, API → 401."""
    if is_authenticated(request):
        return
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        raise NotAuthenticated()
    raise HTTPException(status_code=401, detail="Not authenticated")


async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse(url="/login", status_code=303)
