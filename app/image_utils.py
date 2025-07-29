import base64
import mimetypes
from pathlib import Path


def image_to_base64(image_path: str) -> str:
    """Convert image to base64 data URI."""
    path = Path(image_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = 'application/octet-stream'
    with path.open('rb') as f:
        encoded_bytes = base64.b64encode(f.read())
    encoded_str = encoded_bytes.decode()
    return f"data:{mime_type};base64,{encoded_str}"
