import pytest

from app.services.ai_client import (
    LOCAL_API_KEY_PLACEHOLDER,
    AIClient,
    AIUnavailableError,
)
from app.services.ai_settings import AISettings


class ClientFactoryStub:
    def __init__(self):
        self.calls = []
        self.client = object()

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.client


def test_ai_client_does_not_initialize_without_api_key():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key=None,
        model="test-model",
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    assert client.configured is False
    assert client.status() == {
        "provider": "openai",
        "protocol": "responses",
        "base_url": None,
        "requires_api_key": True,
        "configured": False,
        "enabled": False,
        "active": False,
        "model": "test-model",
        "client_initialized": False,
    }

    with pytest.raises(
        AIUnavailableError,
        match="OPENAI_API_KEY",
    ) as error:
        client.get_client()

    assert error.value.reason == "api_not_configured"
    assert factory.calls == []


def test_ai_client_initializes_with_configured_api_key():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key="test-secret-key",
        model="test-model",
        enabled=True,
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    result = client.get_client()

    assert result is factory.client
    assert factory.calls == [
        {
            "api_key": "test-secret-key",
        }
    ]
    assert client.status()["client_initialized"] is True


def test_ai_client_reuses_initialized_client():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key="test-secret-key",
        model="test-model",
        enabled=True,
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    first = client.get_client()
    second = client.get_client()

    assert first is second
    assert first is factory.client
    assert len(factory.calls) == 1


def test_ai_client_status_does_not_expose_api_key():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key="super-secret-api-key",
        model="test-model",
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    status = client.status()

    assert "api_key" not in status
    assert "super-secret-api-key" not in str(status)


def test_ai_client_does_not_initialize_when_ai_disabled():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key="test-secret-key",
        model="test-model",
        enabled=False,
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    assert client.configured is True

    with pytest.raises(
        AIUnavailableError,
        match="ID_AGENT_AI_ENABLED",
    ) as error:
        client.get_client()

    assert error.value.reason == "ai_disabled"
    assert factory.calls == []


def test_ai_unavailable_error_exposes_reason():
    error = AIUnavailableError(
        "Provider unavailable",
        reason="credit_balance_exhausted",
    )

    assert str(error) == "Provider unavailable"
    assert error.reason == "credit_balance_exhausted"


def test_ai_client_passes_base_url_of_provider():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key="deepseek-key",
        model="deepseek-flash",
        enabled=True,
        provider="deepseek",
        protocol="chat_completions",
        base_url="https://api.deepseek.com",
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    client.get_client()

    assert factory.calls == [
        {
            "api_key": "deepseek-key",
            "base_url": "https://api.deepseek.com",
        }
    ]


def test_ai_client_uses_placeholder_key_for_local_provider():
    factory = ClientFactoryStub()
    settings = AISettings(
        api_key=None,
        model="local-qwen-coder",
        enabled=True,
        provider="local-qwen",
        protocol="chat_completions",
        base_url="http://127.0.0.1:1234/v1",
        requires_api_key=False,
    )
    client = AIClient(
        settings=settings,
        client_factory=factory,
    )

    assert client.configured is True

    client.get_client()

    assert factory.calls == [
        {
            "api_key": LOCAL_API_KEY_PLACEHOLDER,
            "base_url": "http://127.0.0.1:1234/v1",
        }
    ]
