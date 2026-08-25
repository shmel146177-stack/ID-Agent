from collections.abc import Callable
from typing import Any

from openai import OpenAI

from app.services.ai_settings import AISettings


class AIUnavailableError(RuntimeError):
    """AI-сервис не настроен или временно недоступен."""


class AIClient:
    """Безопасная точка доступа к OpenAI для ID-Agent."""

    def __init__(
        self,
        settings: AISettings | None = None,
        client_factory: Callable[..., Any] = OpenAI,
    ):
        self.settings = settings or AISettings.from_environment()
        self.client_factory = client_factory
        self._client = None

    @property
    def configured(self) -> bool:
        return self.settings.configured

    def status(self) -> dict:
        return {
            **self.settings.public_status(),
            "client_initialized": self._client is not None,
        }

    def get_client(self):
        if not self.configured:
            raise AIUnavailableError(
                "OpenAI API не настроен: отсутствует OPENAI_API_KEY"
            )

        if not self.settings.enabled:
            raise AIUnavailableError(
                "AI calls are disabled: set ID_AGENT_AI_ENABLED=true"
            )

        if self._client is None:
            self._client = self.client_factory(
                api_key=self.settings.api_key,
            )

        return self._client
