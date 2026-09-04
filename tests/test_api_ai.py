import pytest

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




def test_ai_analyze_does_not_use_openai_when_disabled(
    monkeypatch,
    tmp_path,
):
    from app.api import ai as ai_module
    from app.services.project_service import project_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "false")

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(tmp_path / "ai_analysis.json"),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(tmp_path / "ai_review.json"),
    )
    monkeypatch.setattr(
        project_service,
        "ai_comparison_file_path",
        str(tmp_path / "ai_comparison.json"),
    )

    def fail_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        raise AssertionError(
            "OpenAI backend must not be initialized"
        )

    monkeypatch.setattr(
        ai_module.AIDocumentAnalysisService,
        "with_openai",
        classmethod(fail_with_openai),
    )

    status_response = client.get("/ai/status")

    assert status_response.status_code == 200
    assert status_response.json() == {
        "provider": "openai",
        "configured": True,
        "enabled": False,
        "active": False,
        "model": "test-model",
        "client_initialized": False,
    }

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Engineering document text.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["requires_human_review"] is True
    assert data["engineering_confirmation"] is False
    assert data["facts"] == []
    assert "document.pdf" in data["summary"]
    assert "backend" in data["summary"]


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

    project_service.save_ai_analysis(
        saved,
        source_filename="document.pdf",
    )

    response = client.get("/ai/latest")

    assert response.status_code == 200

    result = response.json()

    assert result["source_filename"] == "document.pdf"
    assert result["summary"] == saved["summary"]
    assert result["document_type_suggestion"] == "drawing"

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


def test_ai_latest_rejects_missing_analysis_id(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "source_filename": "drawing.pdf",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.get("/ai/latest")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing analysis id",
    }


def test_ai_latest_rejects_missing_source_filename(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "analysis_id": "analysis-1",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.get("/ai/latest")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing source filename",
    }


def test_ai_comparison_returns_saved_comparison(monkeypatch):
    from app.services.project_service import project_service

    saved = {
        "matches": [],
        "conflicts": [],
        "suggestions": [
            {
                "field": "drawing_number",
                "value": "A-01",
                "confidence": 0.95,
            }
        ],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: saved,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "analysis_id": "analysis-123",
            "source_filename": "drawing.pdf",
        },
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 200
    assert response.json() == saved


def test_ai_comparison_returns_404_when_missing(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: None,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI comparison not found",
    }


def test_ai_comparison_rejects_missing_analysis_id_binding(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "source_filename": "drawing.pdf",
    }

    latest_ai = {
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison missing analysis id",
    }


def test_ai_comparison_rejects_missing_current_analysis_id(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
        "source_filename": "drawing.pdf",
    }

    latest_ai = {
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing analysis id",
    }


def test_ai_comparison_rejects_analysis_id_mismatch(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "old-analysis-id",
        "source_filename": "drawing.pdf",
    }

    latest_ai = {
        "analysis_id": "new-analysis-id",
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison analysis id mismatch",
    }


def test_ai_comparison_rejects_missing_source_filename_binding(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
    }

    latest_ai = {
        "analysis_id": "analysis-123",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison missing source filename",
    }


def test_ai_comparison_rejects_missing_current_source_filename(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
        "source_filename": "drawing.pdf",
    }

    latest_ai = {
        "analysis_id": "analysis-123",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing source filename",
    }


def test_ai_comparison_rejects_source_filename_mismatch(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
        "source_filename": "old.pdf",
    }

    latest_ai = {
        "analysis_id": "analysis-123",
        "source_filename": "new.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison source filename mismatch",
    }


def test_ai_comparison_rejects_missing_current_ai_analysis(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-123",
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: None,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison has no current AI analysis",
    }


def test_ai_review_saves_human_decision(monkeypatch):
    from app.services.project_service import project_service

    latest_ai = {
        "summary": "AI suggestion",
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "knowledge_source_ids": ["sp-grounding"],
        "requires_human_review": True,
        "engineering_confirmation": False,
    }

    saved_review = {}

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    def save_ai_review(data):
        saved_review.update(data)

    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        save_ai_review,
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert response.status_code == 200

    expected = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
        "notes": "Checked by human.",
        "knowledge_source_ids": ["sp-grounding"],
    }

    assert response.json() == expected
    assert saved_review == expected


def test_ai_review_returns_404_without_ai_analysis(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: None,
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI analysis not found",
    }


def test_ai_review_rejects_missing_current_analysis_id(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "source_filename": "drawing.pdf",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing analysis id",
    }


def test_ai_review_rejects_missing_current_source_filename(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "analysis_id": "analysis-1",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing source filename",
    }


def test_ai_review_rejects_source_filename_mismatch(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "other.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis source filename mismatch",
    }


def test_ai_review_get_rejects_missing_analysis_id_binding(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "decision": "accepted",
    }

    latest_ai = {
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review missing analysis id",
    }


def test_ai_review_get_rejects_missing_current_analysis_id(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
    }

    latest_ai = {
        "source_filename": "drawing.pdf",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing analysis id",
    }


def test_ai_review_get_rejects_analysis_id_mismatch(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-old",
        "decision": "accepted",
    }

    latest_ai = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-current",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review analysis id mismatch",
    }


def test_ai_review_get_rejects_missing_source_filename_binding(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "analysis_id": "analysis-1",
        "decision": "accepted",
    }

    latest_ai = {
        "analysis_id": "analysis-1",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review missing source filename",
    }


def test_ai_review_get_rejects_missing_current_source_filename(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
    }

    latest_ai = {
        "analysis_id": "analysis-1",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis missing source filename",
    }


def test_ai_review_get_rejects_source_filename_mismatch(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "old.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
    }

    latest_ai = {
        "source_filename": "new.pdf",
        "analysis_id": "analysis-1",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review source filename mismatch",
    }


def test_ai_review_get_rejects_missing_current_ai_analysis(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: None,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review has no current AI analysis",
    }


def test_ai_review_get_returns_saved_review(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
        "notes": "Checked by human.",
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-1",
        },
    )

    response = client.get("/ai/review")

    assert response.status_code == 200
    assert response.json() == saved_review

def test_ai_review_get_returns_404_when_missing(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: None,
    )

    response = client.get("/ai/review")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI review not found",
    }

def test_ai_review_rejects_analysis_id_mismatch(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "AI suggestion",
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-current",
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": "analysis-old",
            "decision": "accepted",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis id mismatch",
    }

def test_ai_analyze_persists_analysis_id(
    monkeypatch,
    tmp_path,
):
    from app.models.ai_analysis import AIAnalysisResult
    from app.services.ai_document_analysis import (
        AIDocumentAnalysisService,
    )
    from app.services.project_service import project_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(tmp_path / "current_ai_analysis.json"),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(tmp_path / "current_ai_review.json"),
    )

    class ServiceStub:
        def analyze_text(self, filename, text):
            return AIAnalysisResult(
                summary="AI analysis completed.",
            )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        return ServiceStub()

    monkeypatch.setattr(
        AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "drawing.pdf",
            "text": "PDF document text",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["source_filename"] == "drawing.pdf"
    assert result["analysis_id"]
    assert result["requires_human_review"] is True
    assert result["engineering_confirmation"] is False

    saved = project_service.get_ai_analysis()

    assert saved == result


def test_ai_analyze_passes_knowledge_context_when_active(monkeypatch):
    from app.services.ai_document_analysis import (
        AIDocumentAnalysisService,
    )
    from app.services.project_service import project_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

    calls = []

    class ServiceStub:
        def analyze_text(
            self,
            filename,
            text,
            knowledge_context=None,
        ):
            calls.append((filename, text, knowledge_context))
            return AIAnalysisResult(
                summary="AI backend selected.",
            )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        return ServiceStub()

    monkeypatch.setattr(
        AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_analysis",
        lambda data, source_filename=None, knowledge_source_ids=None: {
            "document": {
                **data,
                "analysis_id": "analysis-test",
                "source_filename": source_filename,
                "knowledge_source_ids": knowledge_source_ids,
            }
        },
    )

    knowledge_context = (
        "[SOURCE 1]\n"
        "source_id: sp-grounding\n"
        "[/SOURCE]"
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_context": knowledge_context,
        },
    )

    assert response.status_code == 200
    assert calls == [
        (
            "document.pdf",
            "Document text.",
            knowledge_context,
        )
    ]
    assert response.json()["knowledge_source_ids"] == [
        "sp-grounding",
    ]


def test_ai_analyze_rejects_oversized_knowledge_context():
    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_context": "x" * 20_001,
        },
    )

    assert response.status_code == 422


def test_ai_analysis_request_accepts_maximum_knowledge_context():
    from app.api.ai import (
        AIAnalysisRequest,
        MAX_KNOWLEDGE_CONTEXT_CHARS,
    )

    prefix = (
        "[SOURCE 1]\n"
        "source_id: sp-test\n"
        "text:\n"
    )
    suffix = "\n[/SOURCE]"
    content_length = (
        MAX_KNOWLEDGE_CONTEXT_CHARS
        - len(prefix)
        - len(suffix)
    )
    knowledge_context = prefix + ("x" * content_length) + suffix

    request = AIAnalysisRequest(
        filename="document.pdf",
        text="Document text.",
        knowledge_context=knowledge_context,
    )

    assert len(request.knowledge_context) == MAX_KNOWLEDGE_CONTEXT_CHARS


def test_ai_analyze_rejects_knowledge_context_without_source_binding():
    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_context": "Unbound reference text.",
        },
    )

    assert response.status_code == 422


def test_ai_review_get_rejects_knowledge_source_mismatch(monkeypatch):
    from app.services.project_service import project_service

    saved_review = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
        "knowledge_source_ids": ["sp-old"],
    }
    latest_ai = {
        "source_filename": "drawing.pdf",
        "analysis_id": "analysis-1",
        "knowledge_source_ids": ["sp-current"],
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/review")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review knowledge sources mismatch",
    }


def test_ai_comparison_rejects_knowledge_source_mismatch(monkeypatch):
    from app.services.project_service import project_service

    comparison = {
        "matches": [],
        "conflicts": [],
        "suggestions": [],
        "requires_human_review": True,
        "engineering_confirmation": False,
        "analysis_id": "analysis-1",
        "source_filename": "drawing.pdf",
        "knowledge_source_ids": ["sp-old"],
    }
    latest_ai = {
        "analysis_id": "analysis-1",
        "source_filename": "drawing.pdf",
        "knowledge_source_ids": ["sp-current"],
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_comparison",
        lambda: comparison,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )

    response = client.get("/ai/comparison")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI comparison knowledge sources mismatch",
    }

def test_ai_analyze_builds_project_knowledge_context(
    monkeypatch,
    tmp_path,
):
    from app.api import ai as ai_module
    from app.models.knowledge import KnowledgeChunk
    from app.services.knowledge_repository import KnowledgeRepository
    from app.services.project_service import project_service

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

    repository = KnowledgeRepository.for_project("project-a")
    repository.save(
        [
            KnowledgeChunk(
                source_id="project-grounding",
                source_title="Project working documentation",
                page=10,
                text="Grounding requirement for this project.",
            )
        ]
    )

    calls = []

    class ServiceStub:
        def analyze_text(
            self,
            filename,
            text,
            knowledge_context=None,
        ):
            calls.append(
                (filename, text, knowledge_context)
            )
            return AIAnalysisResult(
                summary="AI backend selected.",
            )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        return ServiceStub()

    def save_ai_analysis(
        data,
        source_filename=None,
        knowledge_source_ids=None,
    ):
        return {
            "document": {
                **data,
                "analysis_id": "analysis-project",
                "source_filename": source_filename,
                "knowledge_source_ids": knowledge_source_ids,
            }
        }

    monkeypatch.setattr(
        ai_module.AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_analysis",
        save_ai_analysis,
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_project_name": "project-a",
            "knowledge_query": "grounding",
        },
    )

    assert response.status_code == 200
    assert len(calls) == 1

    knowledge_context = calls[0][2]

    assert "[SOURCE 1]" in knowledge_context
    assert "source_id: project-grounding" in knowledge_context
    assert (
        "Grounding requirement for this project."
        in knowledge_context
    )
    assert response.json()[
        "included_knowledge_pages"
    ] == [
        {
            "source_id": "project-grounding",
            "page": 10,
        }
    ]
    assert response.json()["knowledge_source_ids"] == [
        "project-grounding",
    ]

@pytest.mark.parametrize(
    "project_fields",
    [
        {"knowledge_project_name": "project-a"},
        {"knowledge_query": "grounding"},
        {
            "knowledge_project_name": " ",
            "knowledge_query": "grounding",
        },
        {
            "knowledge_project_name": "project-a",
            "knowledge_query": " ",
        },
    ],
)
def test_ai_analyze_rejects_incomplete_project_knowledge_request(
    monkeypatch,
    project_fields,
):
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "false")

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            **project_fields,
        },
    )

    assert response.status_code == 422

def test_ai_analyze_rejects_invalid_knowledge_project_name(
    monkeypatch,
):
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "false")

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_project_name": "../outside",
            "knowledge_query": "grounding",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith(
        "project_name must"
    )

def test_ai_analyze_rejects_combined_knowledge_modes():
    knowledge_context = (
        "[SOURCE 1]\n"
        "source_id: sp-grounding\n"
        "[/SOURCE]"
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text.",
            "knowledge_context": knowledge_context,
            "knowledge_project_name": "project-a",
            "knowledge_query": "grounding",
        },
    )

    assert response.status_code == 422


def test_ai_analyze_controls_unreviewed_project_ocr(
    monkeypatch,
    tmp_path,
):
    from app.api import ai as ai_module
    from app.models.knowledge import KnowledgeChunk
    from app.services.knowledge_repository import KnowledgeRepository
    from app.services.project_service import project_service

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

    repository = KnowledgeRepository.for_project("project-a")
    repository.save(
        [
            KnowledgeChunk(
                source_id="pending-ocr",
                source_title="Pending OCR",
                page=3,
                text_origin="ocr",
                requires_human_review=True,
                text="Shared safety requirement from pending OCR.",
            )
        ]
    )

    calls = []

    class ServiceStub:
        def analyze_text(
            self,
            filename,
            text,
            knowledge_context=None,
        ):
            calls.append(
                (filename, text, knowledge_context)
            )
            return AIAnalysisResult(
                summary="AI backend selected.",
            )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        return ServiceStub()

    def save_ai_analysis(
        data,
        source_filename=None,
        knowledge_source_ids=None,
    ):
        return {
            "document": {
                **data,
                "analysis_id": "analysis-project-ocr",
                "source_filename": source_filename,
                "knowledge_source_ids": knowledge_source_ids,
            }
        }

    monkeypatch.setattr(
        ai_module.AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_analysis",
        save_ai_analysis,
    )

    default_response = client.post(
        "/ai/analyze",
        json={
            "filename": "default.pdf",
            "text": "Document text.",
            "knowledge_project_name": "project-a",
            "knowledge_query": "safety",
        },
    )
    opt_in_response = client.post(
        "/ai/analyze",
        json={
            "filename": "opt-in.pdf",
            "text": "Document text.",
            "knowledge_project_name": "project-a",
            "knowledge_query": "safety",
            "include_unreviewed_ocr": True,
        },
    )

    assert default_response.status_code == 200
    assert opt_in_response.status_code == 200
    assert len(calls) == 2
    assert default_response.json()[
        "included_knowledge_pages"
    ] == []
    assert opt_in_response.json()[
        "included_knowledge_pages"
    ] == [
        {
            "source_id": "pending-ocr",
            "page": 3,
        }
    ]
    assert default_response.json()[
        "excluded_unreviewed_ocr_pages"
    ] == [
        {
            "source_id": "pending-ocr",
            "page": 3,
        }
    ]
    assert opt_in_response.json()[
        "excluded_unreviewed_ocr_pages"
    ] == []
    assert calls[0][2] is None
    assert "source_id: pending-ocr" in calls[1][2]
    assert "requires_human_review: true" in calls[1][2]


def test_ai_analysis_request_rejects_unreviewed_ocr_flag_without_project():
    from app.api.ai import AIAnalysisRequest

    with pytest.raises(
        ValueError,
        match=(
            "include_unreviewed_ocr requires "
            "project knowledge search"
        ),
    ):
        AIAnalysisRequest(
            filename="document.pdf",
            text="Document text.",
            include_unreviewed_ocr=True,
        )


def test_ai_analyze_saves_autonomous_execution_diagnostics(
    monkeypatch,
    tmp_path,
):
    from app.services.project_service import project_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "false")

    file_paths = {
        "ai_file_path": "ai_analysis.json",
        "ai_review_file_path": "ai_review.json",
        "ai_comparison_file_path": "ai_comparison.json",
    }

    for attribute, filename in file_paths.items():
        monkeypatch.setattr(
            project_service,
            attribute,
            str(tmp_path / filename),
        )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Engineering document text.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["analysis_mode"] == "autonomous"
    assert data["ai_provider"] == "openai"
    assert data["ai_model"] == "test-model"
    assert data["fallback_reason"] == "ai_disabled"

    saved = project_service.get_ai_analysis()

    assert saved["analysis_mode"] == "autonomous"
    assert saved["ai_provider"] == "openai"
    assert saved["ai_model"] == "test-model"
    assert saved["fallback_reason"] == "ai_disabled"
