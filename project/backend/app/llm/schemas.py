from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, model_validator

from app.llm.models import LlmProfile
from app.llm.presets import NO_URL_REQUIRED, PRESETS


class LlmProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    preset: str
    base_url: HttpUrl | None = None
    model: str = Field(min_length=1, max_length=120)
    api_key: SecretStr | None = None
    share_results_with_llm: bool | None = None  # None: the preset default

    @model_validator(mode="after")
    def _check_preset(self) -> Self:
        preset = PRESETS.get(self.preset)
        if preset is None:
            raise ValueError("Unknown preset")
        if preset.base_url is None and self.preset not in NO_URL_REQUIRED and not self.base_url:
            raise ValueError("base_url is required for this preset")
        return self


class LlmProfilePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    preset: str | None = None
    base_url: HttpUrl | None = None
    model: str | None = Field(default=None, min_length=1, max_length=120)
    api_key: SecretStr | None = None  # missing: keep the stored key
    share_results_with_llm: bool | None = None


class LlmProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    preset: str
    base_url: str | None
    model: str
    api_key_hint: str | None
    has_api_key: bool
    share_results_with_llm: bool
    json_mode: bool | None
    is_default: bool
    last_tested_at: datetime | None
    last_test_ok: bool | None

    @classmethod
    def from_profile(cls, p: LlmProfile) -> Self:
        return cls(
            id=p.id,
            name=p.name,
            preset=p.preset,
            base_url=p.base_url or None,
            model=p.model,
            api_key_hint=p.api_key_hint,
            has_api_key=p.api_key_ciphertext is not None,
            share_results_with_llm=p.share_results_with_llm,
            json_mode=p.json_mode,
            is_default=p.is_default,
            last_tested_at=p.last_tested_at,
            last_test_ok=p.last_test_ok,
        )


class PresetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    base_url: str | None
    share_results_default: bool


class ProbeResultOut(BaseModel):
    ok: bool
    json_mode: bool | None = None
    models: list[str] = []
    error: str | None = None
    latency_ms: int
