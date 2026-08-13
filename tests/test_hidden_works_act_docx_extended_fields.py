from pathlib import Path

from docx import Document

from app.generators.hidden_works_act_generator import HiddenWorksActGenerator


def test_hidden_works_act_docx_contains_extended_fields(
    monkeypatch,
    tmp_path,
):

    generator = HiddenWorksActGenerator()

    project_name = "TEST_PROJECT"
    project_path = tmp_path / project_name
    output_folder = project_path / "output"
    project_card_path = project_path / "project_card.json"

    project_path.mkdir(parents=True)

    project_card_path.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        generator,
        "_project_path",
        lambda name: project_path,
    )

    monkeypatch.setattr(
        generator,
        "_project_card_path",
        lambda name: project_card_path,
    )

    monkeypatch.setattr(
        generator,
        "_output_folder",
        lambda name: output_folder,
    )

    registry = {
        "acts_count": 1,
        "acts": [
            {
                "code": "grounding_device",
                "act_title": (
                    "АОСР на устройство "
                    "заземляющего устройства"
                ),
                "priority": "Высокий",
                "evidence": [],
            }
        ],
    }

    act_data = {
        "compliance": (
            "Работы соответствуют проектной документации"
        ),
        "next_works": "Обратная засыпка",
        "remarks": "Замечаний нет",
        "attachments": "Исполнительная схема ИС-01",
    }

    output_file = generator.create(
        project_name,
        act_code="grounding_device",
        registry=registry,
        act_data=act_data,
    )

    document = Document(Path(output_file))

    text_parts = [
        paragraph.text
        for paragraph in document.paragraphs
    ]

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                text_parts.append(cell.text)

    full_text = "\n".join(text_parts)

    assert (
        "Работы соответствуют проектной документации"
        in full_text
    )
    assert "Обратная засыпка" in full_text
    assert "Замечаний нет" in full_text
    assert "Исполнительная схема ИС-01" in full_text
