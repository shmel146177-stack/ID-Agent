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

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
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

    response = client.post(
        "/ai/review",
        json={
            "source_filename": "drawing.pdf",
            "decision": "accepted",
            "notes": "Checked by human.",
        },
    )

    assert response.status_code == 200

    after = project_service.get_ai_analysis()

    assert after == before
    assert after["requires_human_review"] is True
    assert after["engineering_confirmation"] is False

