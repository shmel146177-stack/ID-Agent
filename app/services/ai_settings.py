import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AISettings:
    """Настройки AI/OpenAI-слоя ID-Agent."""

    api_key: str | None
    model: str
    enabled: bool = False

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def from_environment(cls) -> "AISettings":
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or None
        model = (
            os.getenv("OPENAI_MODEL")
            or cls.DEFAULT_MODEL
        ).strip()
        enabled = (
            os.getenv("ID_AGENT_AI_ENABLED") or ""
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        return cls(
            api_key=api_key,
            model=model,
            enabled=enabled,
        )

    @property
    def active(self) -> bool:
        return self.enabled and self.configured

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def public_status(self) -> dict:
        return {
            "provider": "openai",
            "configured": self.configured,
            "model": self.model,
        }
