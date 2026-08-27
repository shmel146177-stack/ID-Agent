from fastapi.testclient import TestClient

from app.services.project_service import project_service
from main import app


client = TestClient(app)



def test_ai_review_persistence_cycle(
    monkeypatch,
    tmp_path,
):
    ai_file = tmp_path / "current_ai_analysis.json"
    review_file = tmp_path / "current_ai_review.json"

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_file),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(review_file),
    )

    project_service.save_ai_analysis(
        {
            "summary": "AI suggestion",
            "document_type_suggestion": "drawing",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
    )

    latest_ai = project_service.get_ai_analysis()
    assert latest_ai is not None

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": latest_ai["analysis_id"],
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert response.status_code == 200
    assert review_file.exists()

    response = client.get("/ai/review")

    assert response.status_code == 200
    assert response.json() == {
        "source_filename": "drawing.pdf",
        "analysis_id": latest_ai["analysis_id"],
        "decision": "accepted",
        "notes": "Checked by human.",
    }

    saved_ai = project_service.get_ai_analysis()

    assert saved_ai is not None
    assert saved_ai["source_filename"] == "drawing.pdf"
    assert saved_ai["engineering_confirmation"] is False


def test_human_review_does_not_modify_ai_analysis(
    monkeypatch,
    tmp_path,
):
    ai_file = tmp_path / "current_ai_analysis.json"
    review_file = tmp_path / "current_ai_review.json"

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_file),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(review_file),
    )

    project_service.save_ai_analysis(
        {
            "summary": "AI suggestion",
            "document_type_suggestion": "drawing",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
    )

    before = project_service.get_ai_analysis()
    assert before is not None

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": before["analysis_id"],
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert response.status_code == 200

    after = project_service.get_ai_analysis()

    assert after == before
    assert after["requires_human_review"] is True
    assert after["engineering_confirmation"] is False


def test_new_ai_analysis_invalidates_saved_review(
    monkeypatch,
    tmp_path,
):
    ai_file = tmp_path / "current_ai_analysis.json"
    review_file = tmp_path / "current_ai_review.json"

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_file),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(review_file),
    )

    project_service.save_ai_analysis(
        {
            "summary": "Old AI analysis",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="old.pdf",
    )

    old_ai = project_service.get_ai_analysis()
    assert old_ai is not None

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "old.pdf",
            "analysis_id": old_ai["analysis_id"],
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert response.status_code == 200
    assert review_file.exists()

    project_service.save_ai_analysis(
        {
            "summary": "New AI analysis",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="new.pdf",
    )

    assert not review_file.exists()

    response = client.get("/ai/review")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "AI review not found",
    }

    response = client.get("/ai/latest")

    assert response.status_code == 200
    assert response.json()["source_filename"] == "new.pdf"

def test_old_analysis_id_is_rejected_after_same_file_reanalysis(
    monkeypatch,
    tmp_path,
):
    ai_file = tmp_path / "current_ai_analysis.json"
    review_file = tmp_path / "current_ai_review.json"

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_file),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(review_file),
    )

    project_service.save_ai_analysis(
        {
            "summary": "First AI analysis",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
    )

    first = project_service.get_ai_analysis()
    assert first is not None

    project_service.save_ai_analysis(
        {
            "summary": "Second AI analysis",
            "facts": [],
            "warnings": [],
            "requires_human_review": True,
            "engineering_confirmation": False,
        },
        source_filename="drawing.pdf",
    )

    second = project_service.get_ai_analysis()
    assert second is not None

    assert first["source_filename"] == second["source_filename"]
    assert first["analysis_id"] != second["analysis_id"]

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "analysis_id": first["analysis_id"],
            "decision": "accepted",
            "notes": "Review of stale analysis.",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "AI analysis id mismatch",
    }

    assert not review_file.exists()

def test_upload_analysis_id_can_be_used_for_review(
    monkeypatch,
    tmp_path,
):
    import app.api.documents as documents_module
    from app.models.ai_analysis import AIAnalysisResult

    ai_file = tmp_path / "current_ai_analysis.json"
    review_file = tmp_path / "current_ai_review.json"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_file),
    )
    monkeypatch.setattr(
        project_service,
        "ai_review_file_path",
        str(review_file),
    )
    monkeypatch.setattr(
        documents_module,
        "UPLOAD_DIR",
        str(upload_dir),
    )

    monkeypatch.setattr(
        documents_module.document_service,
        "analyze",
        lambda file_path: {
            "filename": "drawing.pdf",
            "extension": ".pdf",
            "size_bytes": 8,
            "status": "Document detected",
        },
    )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        lambda file_path: "PDF document text",
    )

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        lambda text: {
            "document_type": "drawing",
        },
    )

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        lambda data: None,
    )

    class AIClientStub:
        class Settings:
            active = True

        def __init__(self):
            self.settings = self.Settings()

    class AIServiceStub:
        @classmethod
        def with_openai(cls, ai_client=None):
            return cls()

        def analyze_text(self, filename, text):
            return AIAnalysisResult(
                summary="AI suggestion",
            )

    monkeypatch.setattr(
        documents_module,
        "AIClient",
        AIClientStub,
    )
    monkeypatch.setattr(
        documents_module,
        "AIDocumentAnalysisService",
        AIServiceStub,
    )

    upload_response = client.post(
        "/upload?use_ai=true",
        files={
            "file": (
                "drawing.pdf",
                b"PDF DATA",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 200

    ai_analysis = upload_response.json()["ai_analysis"]

    assert ai_analysis["source_filename"] == "drawing.pdf"
    assert ai_analysis["analysis_id"]

    review_response = client.post(
        "/ai/review",
        json={
            "source_filename": ai_analysis["source_filename"],
            "analysis_id": ai_analysis["analysis_id"],
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert review_response.status_code == 200
    assert (
        review_response.json()["analysis_id"]
        == ai_analysis["analysis_id"]
    )

