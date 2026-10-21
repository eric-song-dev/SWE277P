from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

FERNET_HELP = (
    "HUB_SECRET_KEY must be a Fernet key; generate one with: "
    'uv run python -c "from cryptography.fernet import Fernet; '
    'print(Fernet.generate_key().decode())"'
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    chatbot_database_url: str
    hub_secret_key: SecretStr
    auth_mode: Literal["none"] = "none"
    display_row_cap: int = 1000
    export_row_cap: int = 100_000
    llm_result_max_rows: int = 200
    llm_result_max_chars: int = 20_000
    llm_timeout_s: float = 30
    statement_timeout_ms: int = 5000
    turn_timeout_s: float = 90
    max_generations: int = 3
    hub_enable_fake_llm: bool = False
    max_upload_bytes: int = 10_485_760
    llm_seed_name: str | None = None
    llm_seed_preset: str | None = None
    llm_seed_base_url: str | None = None
    llm_seed_model: str | None = None
    llm_seed_api_key: SecretStr | None = None
    llm_seed_share_results: str | None = None  # parsed by the seed; empty counts as unset

    @field_validator("hub_secret_key")
    @classmethod
    def _check_fernet_key(cls, value: SecretStr) -> SecretStr:
        try:
            Fernet(value.get_secret_value())
        except (ValueError, TypeError) as exc:
            raise ValueError(FERNET_HELP) from exc
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
