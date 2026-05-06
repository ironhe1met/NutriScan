from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for all AI vision providers."""

    @abstractmethod
    async def analyze(
        self, image_b64: str, media_type: str, model: str | None = None,
    ) -> tuple[str, dict]:
        """Send image to AI and return (raw_text, usage_dict).

        usage_dict keys:
          - input_tokens (int)
          - output_tokens (int)
          - cache_read_tokens (int, optional — Anthropic only)
        """

    @abstractmethod
    def get_models(self) -> dict[str, str]:
        """Return {alias: model_id} mapping."""

    @abstractmethod
    def get_default_model(self) -> str:
        """Return default model alias."""
