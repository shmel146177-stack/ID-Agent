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
        "review_revision": 1,
        "notes": "Checked by human.",
        "knowledge_source_ids": ["sp-grounding"],
    }

    assert response.json() == expected
    assert saved_review == expected


def test_ai_review_saves_structured_excluded_fact_decisions(monkeypatch):
    from app.services.project_service import project_service

    latest_ai = {
        "summary": "Autonomous analysis",
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
            {
                "field": "ip",
                "value": "IP54",
                "reason": "missing_evidence",
                "evidence": None,
            },
        ],
        "requires_human_review": True,
        "engineering_confirmation": False,
    }
    saved_review = {}

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        lambda data: saved_review.update(data),
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "needs_changes",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "corrected",
                    "corrected_value": "230 В",
                    "notes": "Checked against the nameplate.",
                },
                {
                    "field": "ip",
                    "decision": "rejected",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["excluded_fact_reviews"] == [
        {
            "field": "voltage",
            "decision": "corrected",
            "corrected_value": "230 В",
            "notes": "Checked against the nameplate.",
        },
        {
            "field": "ip",
            "decision": "rejected",
            "corrected_value": None,
            "notes": None,
        },
    ]
    assert saved_review == response.json()
    assert latest_ai["engineering_confirmation"] is False


def test_ai_review_rejects_unknown_excluded_fact_field(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "Autonomous analysis",
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "needs_changes",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "accepted",
                },
            ],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Reviewed field is not a current structured "
            "autonomous exclusion"
        ),
    }


def test_ai_review_rejects_acceptance_with_pending_exclusions(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "summary": "Autonomous analysis",
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
                {
                    "field": "ip",
                    "value": "IP54",
                    "reason": "missing_evidence",
                    "evidence": None,
                },
            ],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "accepted",
                },
            ],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "All structured autonomous exclusions must be "
            "reviewed before accepting AI analysis"
        ),
    }


def test_ai_review_accepts_analysis_after_all_exclusions_reviewed(
    monkeypatch,
):
    from app.services.project_service import project_service

    latest_ai = {
        "summary": "Autonomous analysis",
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
            {
                "field": "ip",
                "value": "IP54",
                "reason": "missing_evidence",
                "evidence": None,
            },
        ],
        "requires_human_review": True,
        "engineering_confirmation": False,
    }
    saved_review = {}

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        lambda data: saved_review.update(data),
    )

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "corrected",
                    "corrected_value": "230 В",
                },
                {
                    "field": "ip",
                    "decision": "rejected",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "accepted"
    assert len(response.json()["excluded_fact_reviews"]) == 2
    assert saved_review == response.json()
    assert latest_ai["engineering_confirmation"] is False


def test_excluded_fact_review_statuses_merge_partial_review(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
                {
                    "field": "ip",
                    "value": "IP54",
                    "reason": "missing_evidence",
                    "evidence": None,
                },
            ],
            "engineering_confirmation": False,
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "needs_changes",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "corrected",
                    "corrected_value": "230 В",
                    "notes": "Checked against the nameplate.",
                },
            ],
        },
    )

    response = client.get("/ai/review/exclusions")

    assert response.status_code == 200
    assert response.json() == {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "review_revision": 0,
        "excluded_fact_review_statuses": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
                "review_status": "corrected",
                    "corrected_value": "230 В",
                    "review_notes": "Checked against the nameplate.",
                    "reviewed_by": None,
                    "reviewed_at": None,
            },
            {
                "field": "ip",
                "value": "IP54",
                "reason": "missing_evidence",
                "evidence": None,
                "review_status": "pending",
                    "corrected_value": None,
                    "review_notes": None,
                    "reviewed_by": None,
                    "reviewed_at": None,
            },
        ],
        "excluded_fact_review_summary": {
            "total": 2,
            "reviewed": 1,
            "pending": 1,
            "accepted": 0,
            "rejected": 0,
            "corrected": 1,
            "can_accept": False,
        },
        "engineering_confirmation": False,
    }


def test_excluded_fact_review_statuses_are_pending_without_review(
    monkeypatch,
):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [
                {
                    "field": "ip",
                    "value": "IP54",
                    "reason": "missing_evidence",
                    "evidence": None,
                },
            ],
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: None,
    )

    response = client.get("/ai/review/exclusions")

    assert response.status_code == 200
    assert response.json()["excluded_fact_review_statuses"][0][
        "review_status"
    ] == "pending"
    assert response.json()["excluded_fact_review_summary"] == {
        "total": 1,
        "reviewed": 0,
        "pending": 1,
        "accepted": 0,
        "rejected": 0,
        "corrected": 0,
        "can_accept": False,
    }


def test_excluded_fact_review_summary_allows_fully_reviewed_analysis(
    monkeypatch,
):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
                {
                    "field": "ip",
                    "value": "IP54",
                    "reason": "missing_evidence",
                    "evidence": None,
                },
            ],
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
            "excluded_fact_reviews": [
                {
                    "field": "voltage",
                    "decision": "accepted",
                },
                {
                    "field": "ip",
                    "decision": "rejected",
                },
            ],
        },
    )

    response = client.get("/ai/review/exclusions")

    assert response.status_code == 200
    assert response.json()["excluded_fact_review_summary"] == {
        "total": 2,
        "reviewed": 2,
        "pending": 0,
        "accepted": 1,
        "rejected": 1,
        "corrected": 0,
        "can_accept": True,
    }


def test_single_excluded_fact_review_preserves_existing_decisions(
    monkeypatch,
):
    from app.services.project_service import project_service

    latest_ai = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
            {
                "field": "ip",
                "value": "IP54",
                "reason": "missing_evidence",
                "evidence": None,
            },
        ],
        "engineering_confirmation": False,
    }
    saved_review = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "decision": "needs_changes",
        "notes": None,
        "excluded_fact_reviews": [
            {
                "field": "voltage",
                "decision": "corrected",
                "corrected_value": "230 В",
                "notes": None,
            },
        ],
        "excluded_fact_review_history": [
            {
                "analysis_id": "analysis-1",
                "field": "voltage",
                "action": "created",
                "previous_review": None,
                "current_review": {
                    "field": "voltage",
                    "decision": "corrected",
                    "corrected_value": "230 В",
                    "notes": None,
                },
                "reviewed_by": "Engineer B",
                "reviewed_at": "2026-09-21T10:00:00Z",
            },
        ],
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    def save_ai_review(data):
        saved_review.clear()
        saved_review.update(data)

    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        save_ai_review,
    )

    response = client.put(
        "/ai/review/exclusions/ip",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "rejected",
            "notes": "Not an equipment characteristic.",
            "reviewed_by": "Engineer A",
        },
    )

    assert response.status_code == 200
    fact_reviews = response.json()["excluded_fact_reviews"]
    assert fact_reviews[0] == {
        "field": "voltage",
        "decision": "corrected",
        "corrected_value": "230 В",
        "notes": None,
    }
    assert fact_reviews[1]["field"] == "ip"
    assert fact_reviews[1]["decision"] == "rejected"
    assert fact_reviews[1]["corrected_value"] is None
    assert fact_reviews[1]["notes"] == (
        "Not an equipment characteristic."
    )
    assert fact_reviews[1]["reviewed_by"] == "Engineer A"
    assert fact_reviews[1]["reviewed_at"]
    history = response.json()["excluded_fact_review_history"]
    assert [item["action"] for item in history] == [
        "created",
        "created",
    ]
    assert [item["field"] for item in history] == ["voltage", "ip"]
    assert latest_ai["engineering_confirmation"] is False


def test_single_excluded_fact_review_creates_partial_review(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "knowledge_source_ids": ["passport-source"],
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
            ],
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: None,
    )
    saved_review = {}
    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        lambda data: saved_review.update(data),
    )

    response = client.put(
        "/ai/review/exclusions/voltage",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "accepted",
            "reviewed_by": "Engineer A",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "needs_changes"
    assert response.json()["knowledge_source_ids"] == [
        "passport-source"
    ]
    assert saved_review == response.json()


def test_single_excluded_fact_review_replaces_existing_decision(
    monkeypatch,
):
    from app.services.project_service import project_service

    latest_ai = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
        ],
    }
    saved_review = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "decision": "needs_changes",
        "notes": None,
        "excluded_fact_reviews": [
            {
                "field": "voltage",
                "decision": "rejected",
                "corrected_value": None,
                "notes": None,
            },
        ],
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )
    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        lambda data: None,
    )

    response = client.put(
        "/ai/review/exclusions/voltage",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "decision": "corrected",
            "corrected_value": "230 В",
            "reviewed_by": "Engineer B",
        },
    )

    assert response.status_code == 200
    fact_review = response.json()["excluded_fact_reviews"][0]
    assert fact_review["field"] == "voltage"
    assert fact_review["decision"] == "corrected"
    assert fact_review["corrected_value"] == "230 В"
    assert fact_review["notes"] is None
    assert fact_review["reviewed_by"] == "Engineer B"
    assert fact_review["reviewed_at"]
    history = response.json()["excluded_fact_review_history"]
    assert history[0]["action"] == "updated"
    assert history[0]["previous_review"]["decision"] == "rejected"
    assert history[0]["current_review"]["decision"] == "corrected"


def test_single_excluded_fact_review_rejects_stale_analysis(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-new",
            "excluded_autonomous_facts": [],
        },
    )

    response = client.put(
        "/ai/review/exclusions/voltage",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-old",
            "decision": "accepted",
            "reviewed_by": "Engineer A",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis id mismatch",
    }


def test_single_excluded_fact_review_rejects_stale_revision(monkeypatch):
    from app.services.project_service import project_service

    latest_ai = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
        ],
    }
    saved_review = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "decision": "needs_changes",
        "review_revision": 2,
        "excluded_fact_reviews": [],
    }
    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    response = client.put(
        "/ai/review/exclusions/voltage",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "expected_revision": 1,
            "decision": "accepted",
            "reviewed_by": "Engineer A",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "AI review revision mismatch: expected 1, current 2"
        ),
    }


def test_clear_excluded_fact_review_returns_field_to_pending(monkeypatch):
    from app.services.project_service import project_service

    latest_ai = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "knowledge_source_ids": ["passport-source"],
        "excluded_autonomous_facts": [
            {
                "field": "voltage",
                "value": "220 В",
                "reason": "insufficient_context",
                "evidence": "220 В",
            },
            {
                "field": "ip",
                "value": "IP54",
                "reason": "missing_evidence",
                "evidence": None,
            },
        ],
    }
    saved_review = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-1",
        "decision": "accepted",
        "notes": "All exclusions reviewed.",
        "excluded_fact_reviews": [
            {
                "field": "voltage",
                "decision": "corrected",
                "corrected_value": "230 В",
                "notes": None,
            },
            {
                "field": "ip",
                "decision": "rejected",
                "corrected_value": None,
                "notes": None,
            },
        ],
        "knowledge_source_ids": ["passport-source"],
    }

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: latest_ai,
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: saved_review,
    )

    def save_ai_review(data):
        saved_review.clear()
        saved_review.update(data)

    monkeypatch.setattr(
        project_service,
        "save_ai_review",
        save_ai_review,
    )

    response = client.request(
        "DELETE",
        "/ai/review/exclusions/ip",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "reviewed_by": "Engineer C",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "needs_changes"
    assert response.json()["excluded_fact_reviews"] == [
        {
            "field": "voltage",
            "decision": "corrected",
            "corrected_value": "230 В",
            "notes": None,
        },
    ]
    assert response.json()["knowledge_source_ids"] == [
        "passport-source"
    ]
    assert saved_review == response.json()
    history = response.json()["excluded_fact_review_history"]
    assert history[0]["action"] == "cleared"
    assert history[0]["previous_review"]["field"] == "ip"
    assert history[0]["current_review"] is None
    assert history[0]["reviewed_by"] == "Engineer C"


def test_clear_excluded_fact_review_rejects_missing_decision(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "excluded_autonomous_facts": [
                {
                    "field": "voltage",
                    "value": "220 В",
                    "reason": "insufficient_context",
                    "evidence": "220 В",
                },
            ],
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: None,
    )

    response = client.request(
        "DELETE",
        "/ai/review/exclusions/voltage",
        json={
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-1",
            "reviewed_by": "Engineer A",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Excluded fact review not found",
    }


def test_excluded_fact_review_statuses_reject_stale_review(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_analysis",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-new",
            "excluded_autonomous_facts": [],
        },
    )
    monkeypatch.setattr(
        project_service,
        "get_ai_review",
        lambda: {
            "source_filename": "passport.pdf",
            "analysis_id": "analysis-old",
            "decision": "accepted",
        },
    )

    response = client.get("/ai/review/exclusions")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI review analysis id mismatch",
    }


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


def test_ai_review_history_returns_archived_review(monkeypatch):
    from app.services.project_service import project_service

    archived_review = {
        "source_filename": "passport.pdf",
        "analysis_id": "analysis-old",
        "decision": "accepted",
        "excluded_fact_review_history": [],
    }
    monkeypatch.setattr(
        project_service,
        "get_ai_review_history",
        lambda analysis_id: (
            archived_review
            if analysis_id == "analysis-old"
            else None
        ),
    )

    response = client.get("/ai/review/history/analysis-old")

    assert response.status_code == 200
    assert response.json() == archived_review


def test_ai_review_history_returns_404_for_unknown_analysis(monkeypatch):
    from app.services.project_service import project_service

    monkeypatch.setattr(
        project_service,
        "get_ai_review_history",
        lambda analysis_id: None,
    )

    response = client.get("/ai/review/history/analysis-missing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI review history not found",
    }


def test_ai_review_history_lists_archive_summaries(monkeypatch):
    from app.services.project_service import project_service

    archives = [
        {
            "analysis_id": "analysis-old",
            "source_filename": "passport.pdf",
            "decision": "accepted",
            "archived_at": "2026-09-21T10:00:00+00:00",
            "history_event_count": 3,
        },
    ]
    monkeypatch.setattr(
        project_service,
        "list_ai_review_history",
        lambda: archives,
    )

    response = client.get("/ai/review/history")

    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "total_count": 1,
        "limit": 50,
        "offset": 0,
        "archives": archives,
    }


def test_ai_review_history_paginates_and_filters_archives(monkeypatch):
    from app.services.project_service import project_service

    archives = [
        {
            "analysis_id": "analysis-3",
            "source_filename": "passport.pdf",
        },
        {
            "analysis_id": "analysis-2",
            "source_filename": "drawing.pdf",
        },
        {
            "analysis_id": "analysis-1",
            "source_filename": "passport.pdf",
        },
    ]
    monkeypatch.setattr(
        project_service,
        "list_ai_review_history",
        lambda: archives,
    )

    response = client.get(
        "/ai/review/history",
        params={
            "source_filename": "passport.pdf",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "total_count": 2,
        "limit": 1,
        "offset": 1,
        "archives": [archives[2]],
    }


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 201},
        {"offset": -1},
        {"source_filename": ""},
    ],
)
def test_ai_review_history_rejects_invalid_pagination(params):
    response = client.get("/ai/review/history", params=params)

    assert response.status_code == 422


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
    assert response.json() == {
        **saved_review,
        "review_revision": 0,
    }

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

def test_ai_analyze_saves_credit_balance_fallback_reason(
    monkeypatch,
    tmp_path,
):
    from app.api import ai as ai_module
    from app.services.ai_client import AIUnavailableError
    from app.services.ai_document_analysis import (
        AIDocumentAnalysisService,
    )
    from app.services.project_service import project_service

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("ID_AGENT_AI_ENABLED", "true")

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

    def failing_backend(filename, text):
        raise AIUnavailableError(
            "API balance exhausted",
            reason="credit_balance_exhausted",
        )

    def fake_with_openai(
        cls,
        ai_client=None,
        max_input_chars=40_000,
    ):
        return AIDocumentAnalysisService(
            ai_client=ai_client,
            analysis_backend=failing_backend,
        )

    monkeypatch.setattr(
        ai_module.AIDocumentAnalysisService,
        "with_openai",
        classmethod(fake_with_openai),
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
    assert data["fallback_reason"] == "credit_balance_exhausted"

    saved = project_service.get_ai_analysis()

    assert saved["analysis_mode"] == "autonomous"
    assert saved["ai_provider"] == "openai"
    assert saved["ai_model"] == "test-model"
    assert saved["fallback_reason"] == "credit_balance_exhausted"


def test_ai_analyze_returns_and_saves_autonomous_facts(
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
            "filename": "паспорт.pdf",
            "text": (
                "Паспорт оборудования\n"
                'ООО "Тест"\n'
                "Шкаф управления ШУ-1, 7,5 кВт\n"
                "Степень защиты корпуса: IP54"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()
    facts = {
        fact["field"]: fact["value"]
        for fact in data["facts"]
    }

    assert data["analysis_mode"] == "autonomous"
    assert data["fallback_reason"] == "ai_disabled"
    assert data["document_type_suggestion"] == "Паспорт оборудования"
    assert facts["manufacturer"] == 'ООО "Тест"'
    assert facts["equipment"] == "Шкаф управления ШУ-1, 7,5 кВт"
    assert facts["power"] == "7,5 кВт"
    assert facts["ip"] == "IP54"
    assert data["requires_human_review"] is True
    assert data["engineering_confirmation"] is False

    saved = project_service.get_ai_analysis()

    assert saved["analysis_mode"] == "autonomous"
    assert saved["fallback_reason"] == "ai_disabled"
    assert saved["facts"] == data["facts"]

def test_ai_analyze_returns_and_saves_excluded_autonomous_fact_fields(
    monkeypatch,
    tmp_path,
):
    from app.models.ai_analysis import AutonomousAnalysisResult
    from app.services.autonomous_analysis_backend import (
        AutonomousAnalysisBackend,
    )
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

    def autonomous_backend(self, filename, text):
        return AutonomousAnalysisResult(
            summary="Local analysis completed.",
            excluded_autonomous_fact_fields=[
                "serial_number",
            ],
            excluded_autonomous_fact_reasons={
                "serial_number": "missing_evidence",
            },
            excluded_autonomous_facts=[
                {
                    "field": "serial_number",
                    "value": "ABC-123",
                    "reason": "missing_evidence",
                },
            ],
        )

    monkeypatch.setattr(
        AutonomousAnalysisBackend,
        "__call__",
        autonomous_backend,
    )

    response = client.post(
        "/ai/analyze",
        json={
            "filename": "document.pdf",
            "text": "Document text without a serial number.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["analysis_mode"] == "autonomous"
    assert data["fallback_reason"] == "ai_disabled"
    assert data["excluded_autonomous_fact_fields"] == [
        "serial_number",
    ]
    assert data["excluded_autonomous_fact_reasons"] == {
        "serial_number": "missing_evidence",
    }
    assert data["excluded_autonomous_fact_reason_counts"] == {
        "missing_evidence": 1,
    }
    assert data["excluded_autonomous_facts"] == [
        {
            "field": "serial_number",
            "value": "ABC-123",
            "reason": "missing_evidence",
            "evidence": None,
        },
    ]

    saved = project_service.get_ai_analysis()

    assert saved["excluded_autonomous_fact_fields"] == [
        "serial_number",
    ]
    assert saved["excluded_autonomous_fact_reasons"] == {
        "serial_number": "missing_evidence",
    }
    assert saved["excluded_autonomous_fact_reason_counts"] == {
        "missing_evidence": 1,
    }
    assert saved["excluded_autonomous_facts"] == [
        {
            "field": "serial_number",
            "value": "ABC-123",
            "reason": "missing_evidence",
            "evidence": None,
        },
    ]
