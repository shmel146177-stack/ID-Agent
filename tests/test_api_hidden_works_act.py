from pathlib import Path

from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_creates_hidden_works_act(
    monkeypatch,
    tmp_path,
):

    monkeypatch.chdir(tmp_path)

    project_name = "TEST_PROJECT"

    act_file = tmp_path / "act.docx"
    excel_file = tmp_path / "registry.xlsx"
    zip_file = tmp_path / "package.zip"

    act_file.write_bytes(b"DOCX")
    excel_file.write_bytes(b"XLSX")
    zip_file.write_bytes(b"ZIP")

    saved = {}

    monkeypatch.setattr(
        api_module.hidden_works_act_generator,
        "save_act_data",
        lambda project_name, act_code, act_data: saved.update({
            "project_name": project_name,
            "act_code": act_code,
            "act_data": act_data,
        }) or {"status": "saved"},
    )

    monkeypatch.setattr(
        api_module.hidden_works_act_generator,
        "create",
        lambda project_name, act_code, act_data: str(act_file),
    )

    monkeypatch.setattr(
        api_module.hidden_works_registry,
        "analyze_project",
        lambda project_name: {
            "acts_count": 1,
        },
    )

    monkeypatch.setattr(
        api_module.document_registry_excel,
        "create",
        lambda project_name: str(excel_file),
    )

    monkeypatch.setattr(
        api_module.project_package,
        "create_zip",
        lambda project_name: str(zip_file),
    )

    act = api_module.HiddenWorksActData(
        act_code="grounding_device",
        act_number="1",
        materials="Полоса 40x5 мм",
    )

    response = api_module.create_hidden_works_act(
        project_name,
        act,
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path) == act_file

    assert saved["project_name"] == project_name
    assert saved["act_code"] == "grounding_device"

    assert (
        saved["act_data"]["actual_materials"]
        == "Полоса 40x5 мм"
    )

    assert response.headers["x-act-number"] == "1"
    assert response.headers["x-acts-count"] == "1"
    assert response.headers["x-excel-updated"] == "true"
    assert response.headers["x-package-updated"] == "true"

