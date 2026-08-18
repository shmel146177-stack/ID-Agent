import app.services.project_metadata_service as metadata_module
from app.services.project_metadata_service import ProjectMetadataService


def test_project_metadata_service_updates_missing_fields(monkeypatch, tmp_path):

    service = ProjectMetadataService()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    input_path = project_path / "input"

    input_path.mkdir(parents=True)

    pdf_1 = input_path / "project_1.pdf"
    pdf_2 = input_path / "project_2.pdf"

    pdf_1.write_bytes(b"PDF1")
    pdf_2.write_bytes(b"PDF2")

    service.projects_root = tmp_path

    extracted_text = {
        pdf_1.name: "Текст первого проектного документа",
        pdf_2.name: "Текст второго проектного документа",
    }

    monkeypatch.setattr(
        service,
        "_extract_pdf_text",
        lambda path: extracted_text[path.name],
    )

    analyzed_metadata = {
        "object_name": "ТП-101",
        "address": "Москва",
        "customer": "ООО Заказчик",
        "contractor": "ООО Новый подрядчик",
        "designer": None,
        "chief_engineer": None,
        "contract_number": "15/ТП-2026",
    }

    monkeypatch.setattr(
        metadata_module.project_metadata_analyzer,
        "analyze_text",
        lambda text: dict(analyzed_metadata),
    )

    monkeypatch.setattr(
        service,
        "_extract_project_people_with_ocr",
        lambda pdf_files: {
            "designer": "ООО Проект",
            "chief_engineer": "Иванов И.И.",
        },
    )

    current_project = {
        "object_name": "Существующее название",
        "address": "",
        "customer": "",
        "contractor": "ООО Старый подрядчик",
        "designer": "",
        "chief_engineer": "",
        "contract_number": "",
    }

    monkeypatch.setattr(
        metadata_module.project_manager,
        "get_project",
        lambda name: dict(current_project),
    )

    update_calls = []

    def fake_update_project(name, fields):

        update_calls.append(
            {
                "project": name,
                "fields": dict(fields),
            }
        )

        result = dict(current_project)
        result.update(fields)

        return result

    monkeypatch.setattr(
        metadata_module.project_manager,
        "update_project",
        fake_update_project,
    )

    result = service.update_from_project(
        project_name,
        overwrite=False,
    )

    assert result["project"] == project_name
    assert result["pdf_count"] == 2

    assert result["metadata"]["designer"] == "ООО Проект"
    assert result["metadata"]["chief_engineer"] == "Иванов И.И."
    assert result["metadata"]["contractor"] == "ООО Новый подрядчик"
    assert result["metadata"]["contract_number"] == "15/ТП-2026"

    assert result["updated_fields"]["address"] == "Москва"
    assert result["updated_fields"]["customer"] == "ООО Заказчик"
    assert result["updated_fields"]["designer"] == "ООО Проект"
    assert result["updated_fields"]["chief_engineer"] == "Иванов И.И."
    assert result["updated_fields"]["contract_number"] == "15/ТП-2026"

    assert "object_name" not in result["updated_fields"]
    assert "contractor" not in result["updated_fields"]

    assert len(update_calls) == 1

    assert update_calls[0]["project"] == project_name
    assert update_calls[0]["fields"] == result["updated_fields"]

    assert result["project_card"]["object_name"] == "Существующее название"
    assert result["project_card"]["address"] == "Москва"
    assert result["project_card"]["designer"] == "ООО Проект"
    assert (
        result["project_card"]["contractor"]
        == "ООО Старый подрядчик"
    )
    assert result["project_card"]["contract_number"] == "15/ТП-2026"
