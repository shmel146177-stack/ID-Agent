import os
from dataclasses import dataclass

PROTOCOL_RESPONSES = "responses"
PROTOCOL_CHAT_COMPLETIONS = "chat_completions"
PROTOCOLS = (PROTOCOL_RESPONSES, PROTOCOL_CHAT_COMPLETIONS)

CUSTOM_PROVIDER = "custom"

LOCAL_BASE_URL_MARKERS = ("127.0.0.1", "localhost", "[::1]")


@dataclass(frozen=True)
class AIProviderProfile:
    """Профиль провайдера: протокол, адрес и модель по умолчанию."""

    id: str
    protocol: str
    base_url: str | None
    default_model: str
    requires_api_key: bool = True


@dataclass(frozen=True)
class AISettings:
    """Настройки AI-слоя ID-Agent: провайдер, протокол, адрес, модель и ключ."""

    api_key: str | None
    model: str
    enabled: bool = False
    provider: str = "openai"
    protocol: str = PROTOCOL_RESPONSES
    base_url: str | None = None
    requires_api_key: bool = True

    DEFAULT_PROVIDER = "openai"
    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def from_environment(cls) -> "AISettings":
        """Собрать настройки из переменных окружения.

        Переменные ID_AGENT_AI_* имеют приоритет. Прежние OPENAI_API_KEY и
        OPENAI_MODEL продолжают работать, когда новые не заданы.
        """

        provider_name = _environment_value("ID_AGENT_AI_PROVIDER").lower()
        profile = _provider_profile(provider_name or cls.DEFAULT_PROVIDER)

        protocol = _environment_value("ID_AGENT_AI_PROTOCOL").lower()
        if protocol not in PROTOCOLS:
            protocol = profile.protocol

        base_url = (
            _environment_value("ID_AGENT_AI_BASE_URL") or profile.base_url or None
        )

        model = (
            _environment_value("ID_AGENT_AI_MODEL")
            or _environment_value("OPENAI_MODEL")
            or profile.default_model
            or cls.DEFAULT_MODEL
        )

        api_key = (
            _environment_value("ID_AGENT_AI_API_KEY")
            or _environment_value("OPENAI_API_KEY")
            or None
        )

        requires_api_key = profile.requires_api_key and not _is_local_base_url(base_url)

        return cls(
            api_key=api_key,
            model=model,
            enabled=_is_enabled(_environment_value("ID_AGENT_AI_ENABLED")),
            provider=profile.id,
            protocol=protocol,
            base_url=base_url,
            requires_api_key=requires_api_key,
        )

    @property
    def active(self) -> bool:
        return self.enabled and self.configured

    @property
    def configured(self) -> bool:
        """Провайдеру без ключа (локальный сервер) ключ не нужен."""

        if not self.requires_api_key:
            return True

        return bool(self.api_key)

    def public_status(self) -> dict:
        """Открытые сведения о настройках. Ключ сюда не попадает."""

        return {
            "provider": self.provider,
            "protocol": self.protocol,
            "base_url": self.base_url,
            "requires_api_key": self.requires_api_key,
            "configured": self.configured,
            "enabled": self.enabled,
            "active": self.active,
            "model": self.model,
        }


PROVIDER_PROFILES: dict[str, AIProviderProfile] = {
    "openai": AIProviderProfile(
        id="openai",
        protocol=PROTOCOL_RESPONSES,
        base_url=None,
        default_model=AISettings.DEFAULT_MODEL,
    ),
    "deepseek": AIProviderProfile(
        id="deepseek",
        protocol=PROTOCOL_CHAT_COMPLETIONS,
        base_url="https://api.deepseek.com",
        default_model="deepseek-flash",
    ),
    "local-qwen": AIProviderProfile(
        id="local-qwen",
        protocol=PROTOCOL_CHAT_COMPLETIONS,
        base_url="http://127.0.0.1:1234/v1",
        default_model="local-qwen-coder",
        requires_api_key=False,
    ),
}


def _environment_value(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _is_enabled(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def _is_local_base_url(base_url: str | None) -> bool:
    """Локальный эндпоинт ключа не требует."""

    if not base_url:
        return False

    lowered = base_url.lower()

    return any(marker in lowered for marker in LOCAL_BASE_URL_MARKERS)


def _provider_profile(provider_name: str) -> AIProviderProfile:
    """Профиль известного провайдера либо собственный эндпоинт."""

    known = PROVIDER_PROFILES.get(provider_name)
    if known is not None:
        return known

    return AIProviderProfile(
        id=provider_name or CUSTOM_PROVIDER,
        protocol=PROTOCOL_CHAT_COMPLETIONS,
        base_url=None,
        default_model="",
        requires_api_key=True,
    )
