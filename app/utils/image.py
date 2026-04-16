import base64

from fastapi import UploadFile, HTTPException

from ..config import settings

# Magic bytes for image type detection
_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),  # WebP starts with RIFF....WEBP
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
]


def detect_media_type(data: bytes) -> str | None:
    """Detect image type from file header bytes."""
    for signature, mime in _SIGNATURES:
        if data[:len(signature)] == signature:
            # Extra check for WebP: RIFF is also used by AVI/WAV
            if mime == "image/webp" and data[8:12] != b"WEBP":
                continue
            return mime
    return None


async def process_upload(image: UploadFile) -> tuple[str, str, int]:
    """Read uploaded image, validate, return (base64_data, media_type, size_bytes)."""
    data = await image.read()
    size_bytes = len(data)

    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large: {size_bytes / 1024 / 1024:.1f} MB "
                   f"(max {settings.max_image_size_mb} MB)",
        )

    # Detect type from actual bytes, not filename/content-type
    media_type = detect_media_type(data)
    if not media_type:
        # Fallback to declared content type
        if image.content_type in settings.allowed_image_types:
            media_type = image.content_type
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type. Allowed: {', '.join(sorted(settings.allowed_image_types))}",
            )

    b64 = base64.b64encode(data).decode()
    return b64, media_type, size_bytes
