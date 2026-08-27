from fastapi.testclient import TestClient

from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_settings import AISettings
from main import app


client = TestClient(app)


def test_ai_status_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("ID_AGENT_AI_ENABLED", raising=False)

    response = client.get("/ai/status")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "provider": "openai",
        "configured": False,
        "enabled": False,
        "active": False,
        "model": AISettings.DEFAULT_MODEL,
        "client_initialized": False,
    }


def test_ai_analyze_without_api_key_is_safe(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Текст инженерного документа.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["requires_human_review"] is True
    assert data["engineering_confirmation"] is False
    assert data["facts"] == []
    assert "OpenAI API" in data["summary"]



def test_ai_analyze_uses_openai_when_active(monkeypatch):
    from app.services.ai_document_analysis import (
        AIDocumentAnalysisService,
    )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

    calls = []

    class ServiceStub:
        def analyze_text(self, filename, text):
            calls.append((filename, text))
            return AIAnalysisResult(
                summary="OpenAI backend selected.",
            )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        assert ai_client is not None
        assert ai_client.settings.active is True
        return ServiceStub()

    monkeypatch.setattr(
        AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "????? ??????????? ?????????.",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "OpenAI backend selected."
    assert calls == [
        (
            "document.pdf",
            "????? ??????????? ?????????.",
        )
    ]

def test_ai_latest_returns_saved_analysis(
    monkeypatch,
    tmp_path,
):
    from app.services.project_service import project_service

    saved = {
        "summary": "Saved AI analysis",
        "document_type_suggestion": "drawing",
        "facts": [],
        "warnings": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(tmp_path / "current_ai_analysis.json"),
    )

    project_service.save_ai_analysis(saved)

    response = client.get("/ai/latest")

    assert response.status_code == 200
    assert response.json() == saved

def test_ai_latest_returns_404_when_missing(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: None,
    )

    response = client.get("/ai/latest")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI analysis not found",
    }
