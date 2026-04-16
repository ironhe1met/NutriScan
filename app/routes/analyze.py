import logging
import time

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from ..config import settings
from ..db import log_request
from ..providers.registry import get_provider
from ..utils.image import process_upload
from ..utils.json_parser import extract_and_parse_json

router = APIRouter()
logger = logging.getLogger("nutriscan")


@router.post("/analyze/")
async def analyze(
    image: UploadFile = File(...),
    provider: str | None = Query(None, description="AI provider: anthropic, openai, google"),
    model: str | None = Query(None, description="Model alias (e.g. sonnet, gpt4o, flash)"),
):
    start = time.monotonic()
    provider_name = provider or settings.default_provider
    ai = get_provider(provider_name)
    model_name = model or (
        settings.default_model if provider_name == settings.default_provider
        else ai.get_default_model()
    )

    # Process and validate image
    image_b64, media_type, size_bytes = await process_upload(image)
    logger.info(
        "Received image: %s, %.1f KB, type=%s, provider=%s, model=%s",
        image.filename, size_bytes / 1024, media_type, provider_name, model_name,
    )

    try:
        raw_response = await ai.analyze(image_b64, media_type, model_name)
        result = extract_and_parse_json(raw_response)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "Analysis complete: dish=%s, ingredients=%d, %d ms",
            result.get("dish_name", "?"), len(result.get("ingredients", [])), elapsed_ms,
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

        return {"data": result, "error": None}

    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.error("Analysis failed after %d ms: %s", elapsed_ms, e)

        await log_request(
            provider=provider_name,
            model=model_name,
            response_time_ms=elapsed_ms,
            success=False,
            error=str(e),
            image_size_bytes=size_bytes,
        )

        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")
