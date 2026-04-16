from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator


class Settings(BaseSettings):
    # Default AI provider and model
    default_provider: str = "anthropic"
    default_model: str = "sonnet"

    # Image limits
    max_image_size_mb: int = 10
    allowed_image_types: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}

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

    # App
    debug: bool = False
    api_url: str = "http://127.0.0.1:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
