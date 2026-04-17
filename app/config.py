from typing import Annotated

from pydantic_settings import BaseSettings, NoDecode
from pydantic import SecretStr, field_validator


class Settings(BaseSettings):
    # Default AI provider and model
    default_provider: str = "anthropic"
    default_model: str = "sonnet"

    # Fallback chain: if primary fails, try next in order
    fallback_providers: list[str] = ["anthropic", "openai", "google"]

    @field_validator("fallback_providers", mode="before")
    @classmethod
    def parse_fallback_providers(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    # Image limits
    max_image_size_mb: int = 10
    allowed_image_types: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    # Save uploaded images to disk for history detail view
    store_images: bool = True

    # Provider API keys
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None

    # Telegram bot
    bot_token: SecretStr | None = None
    bot_allowed_users: list[int] = []

    @field_validator("bot_allowed_users", mode="before")
    @classmethod
    def parse_allowed_users(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    # Admin panel auth
    admin_username: str = "admin"
    admin_password: SecretStr | None = None
    # Additional users: "user1:pass1,user2:pass2"
    admin_users: Annotated[dict[str, str], NoDecode] = {}
    session_secret: str = "change-me-to-random-string-in-production"

    @field_validator("admin_users", mode="before")
    @classmethod
    def parse_admin_users(cls, v):
        if isinstance(v, str):
            result = {}
            for pair in v.split(","):
                pair = pair.strip()
                if ":" in pair:
                    user, password = pair.split(":", 1)
                    if user.strip() and password.strip():
                        result[user.strip()] = password.strip()
            return result
        return v

    # App
    debug: bool = False
    api_url: str = "http://127.0.0.1:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
