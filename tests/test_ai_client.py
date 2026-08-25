import pytest

from app.services.ai_client import AIClient, AIUnavailableError
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
        "configured": False,
        "model": "test-model",
        "client_initialized": False,
    }

    with pytest.raises(
        AIUnavailableError,
        match="OPENAI_API_KEY",
    ):
        client.get_client()

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
    ):
        client.get_client()

    assert factory.calls == []
