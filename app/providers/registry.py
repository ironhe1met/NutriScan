from .base import AIProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .google_provider import GoogleProvider
from ..config import settings

_PROVIDERS: dict[str, type[AIProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
}

_instances: dict[str, AIProvider] = {}


def get_provider(name: str | None = None) -> AIProvider:
    """Get or create a provider instance by name. Falls back to default."""
    provider_name = name or settings.default_provider

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(_PROVIDERS)}"
        )

    if provider_name not in _instances:
        _instances[provider_name] = _PROVIDERS[provider_name]()

    return _instances[provider_name]


def list_providers() -> dict:
    """Return available providers and their models."""
    result = {}
    for name, cls in _PROVIDERS.items():
        try:
            provider = get_provider(name)
            result[name] = {
                "available": True,
                "models": provider.get_models(),
                "default_model": provider.get_default_model(),
            }
        except RuntimeError:
            result[name] = {
                "available": False,
                "reason": "API key not configured",
            }
    return result
