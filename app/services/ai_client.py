from collections.abc import Callable
from typing import Any

from openai import OpenAI

from app.services.ai_settings import AISettings

LOCAL_API_KEY_PLACEHOLDER = "local-provider"


class AIUnavailableError(RuntimeError):
    """AI-сервис не настроен или временно недоступен."""

    DEFAULT_REASON = "provider_unavailable"

    def __init__(
        self,
        message: str,
        *,
        reason: str = DEFAULT_REASON,
    ):
        super().__init__(message)
        self.reason = reason


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
                "AI-провайдер не настроен: задайте ID_AGENT_AI_API_KEY "
                "или OPENAI_API_KEY",
                reason="api_not_configured",
            )

        if not self.settings.enabled:
            raise AIUnavailableError(
                "AI calls are disabled: set ID_AGENT_AI_ENABLED=true",
                reason="ai_disabled",
            )

        if self._client is None:
            self._client = self._build_client()

        return self._client

    def _build_client(self):
        """Создать клиент провайдера с учётом адреса и наличия ключа."""

        kwargs: dict[str, Any] = {}

        if self.settings.api_key:
            kwargs["api_key"] = self.settings.api_key
        elif not self.settings.requires_api_key:
            # Локальный сервер ключ не проверяет, но SDK требует значение.
            kwargs["api_key"] = LOCAL_API_KEY_PLACEHOLDER

        if self.settings.base_url:
            kwargs["base_url"] = self.settings.base_url

        return self.client_factory(**kwargs)
