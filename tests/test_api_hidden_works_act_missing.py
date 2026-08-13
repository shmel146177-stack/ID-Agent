import pytest
from fastapi import HTTPException

import app.api.project_processor as api_module


def test_project_api_hidden_works_act_missing_file_returns_404(
    monkeypatch,
    tmp_path,
):

    project_name = "TEST_PROJECT"

    missing_file = tmp_path / "missing_act.docx"
    excel_file = tmp_path / "registry.xlsx"
    package_file = tmp_path / "package.zip"

    excel_file.write_bytes(b"XLSX")
    package_file.write_bytes(b"ZIP")

    monkeypatch.setattr(
        api_module.hidden_works_act_generator,
        "save_act_data",
        lambda project_name, act_code, act_data: {
            "status": "saved",
        },
    )

    monkeypatch.setattr(
        api_module.hidden_works_act_generator,
        "create",
        lambda project_name, act_code, act_data: str(missing_file),
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
        lambda project_name: str(package_file),
    )

    act = api_module.HiddenWorksActData(
        act_code="grounding_device",
        act_number="1",
    )

    with pytest.raises(HTTPException) as error:
        api_module.create_hidden_works_act(
            project_name,
            act,
        )

    assert error.value.status_code == 404
