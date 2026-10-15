import pytest

from app.services.ai_settings import (
    PROTOCOL_CHAT_COMPLETIONS,
    PROTOCOL_RESPONSES,
    AISettings,
)

AI_ENVIRONMENT_VARIABLES = (
    "ID_AGENT_AI_PROVIDER",
    "ID_AGENT_AI_PROTOCOL",
    "ID_AGENT_AI_BASE_URL",
    "ID_AGENT_AI_API_KEY",
    "ID_AGENT_AI_MODEL",
    "ID_AGENT_AI_ENABLED",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
)


@pytest.fixture(autouse=True)
def clear_ai_environment(monkeypatch):
    for name in AI_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_ai_settings_not_configured_without_api_key():
    settings = AISettings.from_environment()

    assert settings.api_key is None
    assert settings.configured is False
    assert settings.model == AISettings.DEFAULT_MODEL
    assert settings.provider == "openai"
    assert settings.protocol == PROTOCOL_RESPONSES
    assert settings.base_url is None
    assert settings.requires_api_key is True
    assert settings.public_status() == {
        "provider": "openai",
        "protocol": PROTOCOL_RESPONSES,
        "base_url": None,
        "requires_api_key": True,
        "configured": False,
        "enabled": False,
        "active": False,
        "model": AISettings.DEFAULT_MODEL,
    }


def test_ai_settings_reads_api_key_and_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "  test-secret-key  ")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    settings = AISettings.from_environment()

    assert settings.api_key == "test-secret-key"
    assert settings.configured is True
    assert settings.model == "test-model"


def test_ai_settings_new_variables_win_over_legacy(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-key")
    monkeypatch.setenv("OPENAI_MODEL", "legacy-model")
    monkeypatch.setenv("ID_AGENT_AI_API_KEY", "new-key")
    monkeypatch.setenv("ID_AGENT_AI_MODEL", "new-model")

    settings = AISettings.from_environment()

    assert settings.api_key == "new-key"
    assert settings.model == "new-model"


def test_ai_settings_public_status_does_not_expose_api_key(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_API_KEY", "super-secret-api-key")

    status = AISettings.from_environment().public_status()

    assert "api_key" not in status
    assert "super-secret-api-key" not in str(status)
    assert status["configured"] is True


def test_ai_settings_treats_blank_api_key_as_missing(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_API_KEY", "   ")

    settings = AISettings.from_environment()

    assert settings.api_key is None
    assert settings.configured is False


def test_ai_settings_ai_disabled_by_default():
    settings = AISettings.from_environment()

    assert settings.enabled is False
    assert settings.active is False


def test_ai_settings_ai_active_only_with_flag_and_key(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = AISettings.from_environment()

    assert settings.enabled is True
    assert settings.configured is True
    assert settings.active is True


def test_ai_settings_uses_default_model_for_blank_value(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "   ")

    assert AISettings.from_environment().model == AISettings.DEFAULT_MODEL


def test_ai_settings_deepseek_profile(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("ID_AGENT_AI_API_KEY", "deepseek-key")

    settings = AISettings.from_environment()

    assert settings.provider == "deepseek"
    assert settings.protocol == PROTOCOL_CHAT_COMPLETIONS
    assert settings.base_url == "https://api.deepseek.com"
    assert settings.model == "deepseek-flash"
    assert settings.requires_api_key is True
    assert settings.configured is True


def test_ai_settings_local_provider_needs_no_api_key(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "local-qwen")

    settings = AISettings.from_environment()

    assert settings.provider == "local-qwen"
    assert settings.protocol == PROTOCOL_CHAT_COMPLETIONS
    assert settings.base_url == "http://127.0.0.1:1234/v1"
    assert settings.model == "local-qwen-coder"
    assert settings.api_key is None
    assert settings.requires_api_key is False
    assert settings.configured is True


def test_ai_settings_custom_provider_reads_endpoint_and_model(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "custom")
    monkeypatch.setenv("ID_AGENT_AI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("ID_AGENT_AI_MODEL", "my-model")
    monkeypatch.setenv("ID_AGENT_AI_API_KEY", "custom-key")

    settings = AISettings.from_environment()

    assert settings.provider == "custom"
    assert settings.protocol == PROTOCOL_CHAT_COMPLETIONS
    assert settings.base_url == "https://gateway.example/v1"
    assert settings.model == "my-model"
    assert settings.configured is True


def test_ai_settings_unknown_provider_uses_chat_completions(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "my-relay")

    settings = AISettings.from_environment()

    assert settings.provider == "my-relay"
    assert settings.protocol == PROTOCOL_CHAT_COMPLETIONS


def test_ai_settings_explicit_protocol_wins(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("ID_AGENT_AI_PROTOCOL", "responses")

    assert AISettings.from_environment().protocol == PROTOCOL_RESPONSES


def test_ai_settings_ignores_unknown_protocol(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("ID_AGENT_AI_PROTOCOL", "grpc")

    assert AISettings.from_environment().protocol == PROTOCOL_CHAT_COMPLETIONS


def test_ai_settings_local_endpoint_removes_key_requirement(monkeypatch):
    monkeypatch.setenv("ID_AGENT_AI_PROVIDER", "custom")
    monkeypatch.setenv("ID_AGENT_AI_BASE_URL", "http://localhost:1234/v1")

    settings = AISettings.from_environment()

    assert settings.requires_api_key is False
    assert settings.configured is True
