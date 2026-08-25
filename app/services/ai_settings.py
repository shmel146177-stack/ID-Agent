import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AISettings:
    """Настройки AI/OpenAI-слоя ID-Agent."""

    api_key: str | None
    model: str

    DEFAULT_MODEL = "gpt-5-mini"

    @classmethod
    def from_environment(cls) -> "AISettings":
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or None
        model = (
            os.getenv("OPENAI_MODEL")
            or cls.DEFAULT_MODEL
        ).strip()

        return cls(
            api_key=api_key,
            model=model,
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def public_status(self) -> dict:
        return {
            "provider": "openai",
            "configured": self.configured,
            "model": self.model,
        }
