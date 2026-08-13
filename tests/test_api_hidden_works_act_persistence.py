import json
from pathlib import Path

from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_persists_hidden_works_act_data(
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
        act_number="А-003",
        compliance="Соответствует проекту",
        next_works="Обратная засыпка",
        remarks="Замечаний нет",
        attachments="Исполнительная схема ИС-03",
    )

    response = api_module.create_hidden_works_act(
        project_name,
        act,
    )

    assert isinstance(response, FileResponse)

    storage_path = (
        Path("projects")
        / project_name
        / "hidden_works_act_data.json"
    )

    assert storage_path.is_file()

    data = json.loads(
        storage_path.read_text(
            encoding="utf-8",
        )
    )

    saved = data["acts"]["grounding_device"]

    assert saved["act_number"] == "А-003"
    assert saved["compliance"] == "Соответствует проекту"
    assert saved["next_works"] == "Обратная засыпка"
    assert saved["remarks"] == "Замечаний нет"
    assert (
        saved["attachments"]
        == "Исполнительная схема ИС-03"
    )
