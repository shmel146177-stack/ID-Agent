from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.project_service import (
    ProjectService,
    ProjectStateCorruptionError,
    project_service,
)
from main import app


client = TestClient(app)


@pytest.mark.parametrize(
    ("path_attribute", "getter_name", "state_name"),
    [
        ("file_path", "get_analysis", "deterministic analysis"),
        ("ai_file_path", "get_ai_analysis", "AI analysis"),
        ("ai_review_file_path", "get_ai_review", "AI review"),
        (
            "ai_comparison_file_path",
            "get_ai_comparison",
            "AI comparison",
        ),
    ],
)
def test_project_service_reports_corrupted_current_state(
    tmp_path,
    path_attribute,
    getter_name,
    state_name,
):
    service = ProjectService()
    state_path = tmp_path / f"{path_attribute}.json"
    state_path.write_text('{"incomplete":', encoding="utf-8")
    setattr(service, path_attribute, str(state_path))

    with pytest.raises(
        ProjectStateCorruptionError,
        match=state_name,
    ) as captured:
        getattr(service, getter_name)()

    assert captured.value.state_name == state_name
    assert captured.value.reason == "invalid JSON at line 1, column 15"


def test_project_service_rejects_non_object_state(tmp_path):
    service = ProjectService()
    state_path = tmp_path / "current_ai_review.json"
    state_path.write_text("[]", encoding="utf-8")
    service.ai_review_file_path = str(state_path)

    with pytest.raises(
        ProjectStateCorruptionError,
        match="top-level JSON value must be an object",
    ):
        service.get_ai_review()


def test_project_service_reports_invalid_state_encoding(tmp_path):
    service = ProjectService()
    state_path = tmp_path / "current_ai_analysis.json"
    state_path.write_bytes(b"\xff\xfe")
    service.ai_file_path = str(state_path)

    with pytest.raises(
        ProjectStateCorruptionError,
        match="invalid UTF-8 encoding",
    ):
        service.get_ai_analysis()


def test_project_service_reports_corrupted_review_archive(tmp_path):
    service = ProjectService()
    service.ai_review_history_dir = str(tmp_path)
    archive_path = Path(
        service._ai_review_history_path("analysis-1")
    )
    archive_path.write_text('{"analysis_id":', encoding="utf-8")

    with pytest.raises(
        ProjectStateCorruptionError,
        match="AI review archive",
    ):
        service.get_ai_review_history("analysis-1")


def test_api_reports_corrupted_state_without_modifying_file(
    monkeypatch,
    tmp_path,
):
    ai_path = tmp_path / "current_ai_analysis.json"
    corrupted_bytes = b'{"analysis_id":'
    ai_path.write_bytes(corrupted_bytes)
    monkeypatch.setattr(
        project_service,
        "ai_file_path",
        str(ai_path),
    )

    response = client.get("/ai/review/exclusions")

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Corrupted project state file 'AI analysis': "
            "invalid JSON at line 1, column 16"
        ),
    }
    assert ai_path.read_bytes() == corrupted_bytes
