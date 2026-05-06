import base64

from google import genai
from google.genai import types

from .base import AIProvider
from ..config import settings
from ..prompt import SYSTEM_PROMPT


class GoogleProvider(AIProvider):
    MODELS = {
        "flash": "gemini-2.0-flash",
        "flash-lite": "gemini-2.0-flash-lite",
        "pro": "gemini-2.5-pro-preview-05-06",
    }

    def __init__(self):
        key = settings.google_api_key
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        self.client = genai.Client(api_key=key.get_secret_value())

    def get_models(self) -> dict[str, str]:
        return self.MODELS

    def get_default_model(self) -> str:
        return "flash"

    async def analyze(
        self, image_b64: str, media_type: str, model: str | None = None,
    ) -> tuple[str, dict]:
        model_alias = model or self.get_default_model()
        model_id = self.MODELS.get(model_alias)
        if not model_id:
            raise ValueError(f"Unknown model '{model_alias}'. Available: {list(self.MODELS)}")

        image_bytes = base64.b64decode(image_b64)

        response = await self.client.aio.models.generate_content(
            model=model_id,
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                        types.Part.from_text(text="Analyze this food image."),
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=4096,
            ),
        )
        meta = getattr(response, "usage_metadata", None)
        usage = {
            "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
            "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            "cache_read_tokens": 0,
        }
        return response.text, usage
