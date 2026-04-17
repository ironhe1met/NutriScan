import logging
import time

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response

from ..config import settings
from ..db import log_request
from ..providers.registry import get_provider
from ..utils.image import process_upload
from ..utils.json_parser import extract_and_parse_json

router = APIRouter()
logger = logging.getLogger("nutriscan")


def _build_fallback_chain(requested_provider: str) -> list[str]:
    """Build the order: requested provider first, then fallbacks (deduplicated)."""
    chain = [requested_provider]
    for p in settings.fallback_providers:
        if p not in chain:
            chain.append(p)
    return chain


@router.post("/analyze/")
async def analyze(
    response: Response,
    image: UploadFile = File(...),
    provider: str | None = Query(None, description="AI provider: anthropic, openai, google"),
    model: str | None = Query(None, description="Model alias (e.g. sonnet, gpt4o, flash)"),
):
    start = time.monotonic()
    requested_provider = provider or settings.default_provider
    requested_model = model

    # Process and validate image (before any provider calls)
    image_b64, media_type, size_bytes = await process_upload(image)
    logger.info(
        "Received image: %s, %.1f KB, type=%s, requested=%s/%s",
        image.filename, size_bytes / 1024, media_type,
        requested_provider, requested_model or "default",
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
            raw_response = await ai.analyze(image_b64, media_type, use_model)
            result = extract_and_parse_json(raw_response)

            elapsed_ms = int((time.monotonic() - start) * 1000)
            fallback_used = attempt_idx > 0

            logger.info(
                "Analysis complete via %s/%s (attempt %d): dish=%s, ingredients=%d, %d ms",
                provider_name, model_name, attempt_idx + 1,
                result.get("dish_name", "?"),
                len(result.get("ingredients", [])),
                elapsed_ms,
            )

            await log_request(
                provider=provider_name,
                model=model_name,
                response_time_ms=elapsed_ms,
                success=True,
                dish_name=result.get("dish_name"),
                image_size_bytes=size_bytes,
                ingredients_count=len(result.get("ingredients", [])),
                result_json=result,
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
