import base64
import hashlib
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Query, Request, Response

from ..config import settings
from ..db import log_request, get_client_by_token_hash
from ..pricing import compute_cost
from ..providers.registry import get_provider
from ..utils.image import process_upload
from ..utils.json_parser import extract_and_parse_json

router = APIRouter()
logger = logging.getLogger("nutriscan")

IMAGES_DIR = Path("data/images")
_EXT_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _save_image(image_b64: str, media_type: str) -> str | None:
    """Save decoded image to disk, return filename or None on error."""
    if not settings.store_images:
        return None
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        ext = _EXT_MAP.get(media_type, ".bin")
        filename = f"{uuid4().hex}{ext}"
        (IMAGES_DIR / filename).write_bytes(base64.b64decode(image_b64))
        return filename
    except Exception as e:
        logger.warning("Failed to save image: %s", e)
        return None


def _build_fallback_chain(requested_provider: str) -> list[str]:
    """Build the order: requested provider first, then fallbacks (deduplicated)."""
    chain = [requested_provider]
    for p in settings.fallback_providers:
        if p not in chain:
            chain.append(p)
    return chain


async def _resolve_client(authorization: str | None) -> tuple[int | None, str | None]:
    """Returns (client_id, client_name) or (None, None) for anonymous requests.

    Phase-1 rollout: token is OPTIONAL — no token, or invalid token, both end up as anon.
    """
    if not authorization:
        return None, None
    if not authorization.lower().startswith("bearer "):
        return None, None
    token = authorization[7:].strip()
    if not token:
        return None, None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    client = await get_client_by_token_hash(token_hash)
    if client:
        return client["id"], client["name"]
    return None, None


@router.post("/analyze/")
async def analyze(
    response: Response,
    request: Request,
    image: UploadFile = File(...),
    provider: str | None = Query(None, description="AI provider: anthropic, openai, google"),
    model: str | None = Query(None, description="Model alias (e.g. sonnet, gpt4o, flash)"),
    authorization: str | None = Header(None),
    x_telegram_user_id: int | None = Header(None),
):
    start = time.monotonic()
    requested_provider = provider or settings.default_provider
    requested_model = model

    # Phase-1 token check (optional, anonymous allowed)
    client_id, client_name = await _resolve_client(authorization)

    # Process and validate image (before any provider calls)
    image_b64, media_type, size_bytes = await process_upload(image)
    logger.info(
        "Received image: %s, %.1f KB, type=%s, requested=%s/%s, client=%s, tg_user=%s",
        image.filename, size_bytes / 1024, media_type,
        requested_provider, requested_model or "default",
        client_name or "anon", x_telegram_user_id or "-",
    )

    # Try each provider in the fallback chain
    chain = _build_fallback_chain(requested_provider)
    errors = []

    for attempt_idx, provider_name in enumerate(chain):
        # Use user's requested model only on first attempt; fallbacks use provider default
        use_model = requested_model if attempt_idx == 0 else None

        try:
            ai = get_provider(provider_name)
        except (ValueError, RuntimeError) as e:
            errors.append(f"{provider_name}: {e}")
            logger.warning("Skipping %s: %s", provider_name, e)
            continue

        model_name = use_model or ai.get_default_model()

        try:
            raw_response, usage = await ai.analyze(image_b64, media_type, use_model)
            result = extract_and_parse_json(raw_response)

            elapsed_ms = int((time.monotonic() - start) * 1000)
            fallback_used = attempt_idx > 0

            # Resolve full model id for pricing lookup (alias → id)
            model_id_for_pricing = ai.get_models().get(model_name, model_name)
            cost = compute_cost(
                provider_name,
                model_id_for_pricing,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                usage.get("cache_read_tokens", 0),
            )

            logger.info(
                "Analysis complete via %s/%s (attempt %d): dish=%s, ingredients=%d, "
                "%d ms, in=%d out=%d cost=%s",
                provider_name, model_name, attempt_idx + 1,
                result.get("dish_name", "?"),
                len(result.get("ingredients", [])),
                elapsed_ms,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                f"${cost:.4f}" if cost is not None else "—",
            )

            image_filename = _save_image(image_b64, media_type)

            await log_request(
                provider=provider_name,
                model=model_name,
                response_time_ms=elapsed_ms,
                success=True,
                dish_name=result.get("dish_name"),
                image_size_bytes=size_bytes,
                ingredients_count=len(result.get("ingredients", [])),
                result_json=result,
                image_filename=image_filename,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cache_read_tokens=usage.get("cache_read_tokens", 0),
                cost_usd=cost,
                client_id=client_id,
                telegram_user_id=x_telegram_user_id,
            )

            # Expose actual provider/model via response headers (doesn't break mobile JSON contract)
            response.headers["X-Provider"] = provider_name
            response.headers["X-Model"] = model_name
            response.headers["X-Attempts"] = str(attempt_idx + 1)
            if fallback_used:
                response.headers["X-Fallback-From"] = requested_provider

            return {"data": result, "error": None}

        except Exception as e:
            err_msg = f"{provider_name}/{model_name}: {type(e).__name__}: {e}"
            errors.append(err_msg)
            logger.warning("Attempt %d failed (%s)", attempt_idx + 1, err_msg)

            # Log failure for stats
            elapsed_ms = int((time.monotonic() - start) * 1000)
            await log_request(
                provider=provider_name,
                model=model_name,
                response_time_ms=elapsed_ms,
                success=False,
                error=str(e),
                image_size_bytes=size_bytes,
                client_id=client_id,
                telegram_user_id=x_telegram_user_id,
            )
            # Continue to next provider
            continue

    # All providers failed
    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.error("All %d providers failed after %d ms: %s", len(chain), elapsed_ms, errors)
    raise HTTPException(
        status_code=503,
        detail=f"All AI providers failed: {'; '.join(errors)}",
    )
