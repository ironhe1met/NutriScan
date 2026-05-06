from openai import AsyncOpenAI

from .base import AIProvider
from ..config import settings
from ..prompt import SYSTEM_PROMPT


class OpenAIProvider(AIProvider):
    MODELS = {
        "gpt4o": "gpt-4o",
        "gpt4o-mini": "gpt-4o-mini",
    }

    def __init__(self):
        key = settings.openai_api_key
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = AsyncOpenAI(api_key=key.get_secret_value())

    def get_models(self) -> dict[str, str]:
        return self.MODELS

    def get_default_model(self) -> str:
        return "gpt4o"

    async def analyze(
        self, image_b64: str, media_type: str, model: str | None = None,
    ) -> tuple[str, dict]:
        model_alias = model or self.get_default_model()
        model_id = self.MODELS.get(model_alias)
        if not model_id:
            raise ValueError(f"Unknown model '{model_alias}'. Available: {list(self.MODELS)}")

        response = await self.client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this food image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}",
                            },
                        },
                    ],
                },
            ],
            max_tokens=4096,
        )
        usage = {
            "input_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
            "output_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
            "cache_read_tokens": 0,
        }
        return response.choices[0].message.content, usage
