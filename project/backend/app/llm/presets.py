from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    base_url: str | None
    share_results_default: bool


PRESETS: dict[str, Preset] = {
    p.key: p
    for p in (
        Preset("zotgpt", "ZotGPT Gateway", None, True),
        Preset("openai", "OpenAI", "https://api.openai.com/v1", False),
        Preset("deepseek", "DeepSeek", "https://api.deepseek.com", False),
        Preset("custom", "Custom (OpenAI-compatible)", None, False),
        Preset("fake", "Demo (scripted)", None, True),
    )
}

# `fake` needs neither a base URL nor a key.
NO_URL_REQUIRED = {"fake"}


def available_presets(settings: Settings) -> list[Preset]:
    return [p for p in PRESETS.values() if p.key != "fake" or settings.hub_enable_fake_llm]
