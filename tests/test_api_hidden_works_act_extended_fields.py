from pathlib import Path

from fastapi.responses import FileResponse

import app.api.project_processor as api_module


def test_project_api_passes_extended_hidden_works_act_fields(
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

    def fake_save_act_data(
        project_name,
        act_code,
        act_data,
    ):
        saved["project_name"] = project_name
        saved["act_code"] = act_code
        saved["act_data"] = act_data

        return {"status": "saved"}

    monkeypatch.setattr(
        api_module.hidden_works_act_generator,
        "save_act_data",
        fake_save_act_data,
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
        act_number="А-002",
        compliance="Работы соответствуют проектной документации",
        next_works="Обратная засыпка",
        remarks="Замечаний нет",
        attachments="Исполнительная схема ИС-01",
        materials_compliance="Materials comply with project",
        test_results="Test protocol 15",
        geometric_parameters="Elevation matches project",
    )

    response = api_module.create_hidden_works_act(
        project_name,
        act,
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path) == act_file

    act_data = saved["act_data"]

    assert (
        act_data["compliance"]
        == "Работы соответствуют проектной документации"
    )
    assert act_data["next_works"] == "Обратная засыпка"
    assert act_data["remarks"] == "Замечаний нет"
    assert (
        act_data["attachments"]
        == "Исполнительная схема ИС-01"
    )
    assert (
        act_data["materials_compliance"]
        == "Materials comply with project"
    )
    assert act_data["test_results"] == "Test protocol 15"
    assert (
        act_data["geometric_parameters"]
        == "Elevation matches project"
    )
