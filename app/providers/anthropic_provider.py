import anthropic

from .base import AIProvider
from ..config import settings
from ..prompt import SYSTEM_PROMPT


class AnthropicProvider(AIProvider):
    MODELS = {
        "opus": "claude-opus-4-6",
        "sonnet": "claude-sonnet-4-6",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(self):
        key = settings.anthropic_api_key
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.AsyncAnthropic(api_key=key.get_secret_value())

    def get_models(self) -> dict[str, str]:
        return self.MODELS

    def get_default_model(self) -> str:
        return "sonnet"

    async def analyze(
        self, image_b64: str, media_type: str, model: str | None = None,
    ) -> tuple[str, dict]:
        model_alias = model or self.get_default_model()
        model_id = self.MODELS.get(model_alias)
        if not model_id:
            raise ValueError(f"Unknown model '{model_alias}'. Available: {list(self.MODELS)}")

        response = await self.client.messages.create(
            model=model_id,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Analyze this food image.",
                        },
                    ],
                }
            ],
        )
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
            "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
        }
        return response.content[0].text, usage
