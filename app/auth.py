import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import settings

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Dependency that protects routes with Basic Auth."""
    if not settings.admin_password:
        return  # no password set = no protection (dev mode)

    correct_user = secrets.compare_digest(
        credentials.username.encode(), settings.admin_username.encode()
    )
    correct_pass = secrets.compare_digest(
        credentials.password.encode(), settings.admin_password.get_secret_value().encode()
    )

    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
