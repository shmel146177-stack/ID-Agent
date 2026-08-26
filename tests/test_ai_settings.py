from app.services.ai_settings import AISettings


def test_ai_settings_not_configured_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("ID_AGENT_AI_ENABLED", raising=False)

    settings = AISettings.from_environment()

    assert settings.api_key is None
    assert settings.configured is False
    assert settings.model == AISettings.DEFAULT_MODEL
    assert settings.public_status() == {
        "provider": "openai",
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


def test_ai_settings_public_status_does_not_expose_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-api-key")

    settings = AISettings.from_environment()
    status = settings.public_status()

    assert "api_key" not in status
    assert "super-secret-api-key" not in str(status)
    assert status["configured"] is True


def test_ai_settings_treats_blank_api_key_as_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "   ")

    settings = AISettings.from_environment()

    assert settings.api_key is None
    assert settings.configured is False


def test_ai_settings_ai_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ID_AGENT_AI_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

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
