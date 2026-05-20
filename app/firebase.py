"""Firebase Admin SDK wrapper — read-only profile fetch for mobile users.

Designed to fail gracefully:
- If credential file is missing → log info once, every call returns None.
- If file exists but SA has no roles (403 from Auth/Firestore) → log warning per call, return None.
- If UID does not exist → return None.
The HTTP request to /analyze/ NEVER fails because of Firebase issues.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from .config import settings

logger = logging.getLogger("nutriscan.firebase")

_initialized: bool = False
_init_error: str | None = None
_app = None  # type: ignore[assignment]
_firestore_client = None  # type: ignore[assignment]


def _try_init() -> None:
    """Lazy idempotent init. Sets module-level `_initialized` / `_init_error`."""
    global _initialized, _init_error, _app, _firestore_client
    if _initialized or _init_error:
        return

    cred_path = Path(settings.firebase_cred_path)
    if not cred_path.exists():
        _init_error = f"Firebase credential file not found: {cred_path}"
        logger.info(_init_error + " — Firebase integration disabled.")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as e:
        _init_error = f"firebase-admin not installed: {e}"
        logger.warning(_init_error)
        return

    try:
        cred = credentials.Certificate(str(cred_path))
        _app = firebase_admin.initialize_app(cred)
        _firestore_client = firestore.client()
        _initialized = True
        logger.info("Firebase initialized: project_id=%s", cred.project_id)
    except Exception as e:
        _init_error = f"Firebase init failed: {type(e).__name__}: {e}"
        logger.warning(_init_error)


def is_enabled() -> bool:
    _try_init()
    return _initialized


def _fetch_profile_sync(uid: str) -> dict[str, Any] | None:
    """Synchronous fetch — runs in thread pool. Returns dict or None on any error."""
    if not is_enabled():
        return None

    from firebase_admin import auth as fb_auth
    from firebase_admin import exceptions as fb_exc
    from google.api_core import exceptions as gcp_exc

    profile: dict[str, Any] = {"uid": uid}

    # 1. Auth profile
    try:
        user = fb_auth.get_user(uid)
        profile.update({
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "disabled": user.disabled,
            "email_verified": user.email_verified,
            "phone_number": user.phone_number,
            "provider_ids": [p.provider_id for p in (user.provider_data or [])],
            "custom_claims": user.custom_claims or {},
            "created_at": (user.user_metadata.creation_timestamp if user.user_metadata else None),
            "last_sign_in_at": (
                user.user_metadata.last_sign_in_timestamp if user.user_metadata else None
            ),
        })
    except fb_auth.UserNotFoundError:
        logger.info("Firebase Auth: user not found uid=%s", uid)
        return None
    except (fb_exc.PermissionDeniedError, gcp_exc.PermissionDenied) as e:
        logger.warning(
            "Firebase Auth: permission denied for uid=%s — "
            "service account likely missing 'Firebase Authentication Viewer' role (%s)",
            uid, e,
        )
        profile["_auth_error"] = "permission_denied"
    except Exception as e:
        logger.warning("Firebase Auth fetch failed for uid=%s: %s: %s", uid, type(e).__name__, e)
        profile["_auth_error"] = f"{type(e).__name__}"

    # 2. Firestore users/{uid} document
    try:
        doc = _firestore_client.collection("users").document(uid).get()
        if doc.exists:
            profile["firestore"] = doc.to_dict() or {}
        else:
            profile["firestore"] = None
    except (gcp_exc.PermissionDenied,) as e:
        logger.warning(
            "Firestore: permission denied for uid=%s — "
            "service account likely missing 'Cloud Datastore Viewer' role (%s)",
            uid, e,
        )
        profile["_firestore_error"] = "permission_denied"
    except Exception as e:
        logger.warning(
            "Firestore fetch failed for uid=%s: %s: %s", uid, type(e).__name__, e
        )
        profile["_firestore_error"] = f"{type(e).__name__}"

    return profile


async def get_user_profile(uid: str) -> dict[str, Any] | None:
    """Async wrapper around the blocking Firebase call (runs in thread pool)."""
    if not uid or not is_enabled():
        return None
    return await asyncio.to_thread(_fetch_profile_sync, uid)


def get_init_error() -> str | None:
    """For diagnostic UIs: why Firebase is not enabled."""
    _try_init()
    return _init_error
