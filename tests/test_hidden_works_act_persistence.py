from pathlib import Path

from app.generators.hidden_works_act_generator import HiddenWorksActGenerator


def test_hidden_works_act_data_persistence(monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    project_name = "TEST_PROJECT"
    act_code = "grounding_device"

    project_path = Path("projects") / project_name
    project_path.mkdir(parents=True)

    generator = HiddenWorksActGenerator()

    act_data = {
        "act_number": "А-001",
        "compliance": "Работы соответствуют проектной документации",
        "next_works": "Обратная засыпка",
        "remarks": "Замечаний нет",
        "attachments": "Исполнительная схема ИС-01",
        "materials_compliance": "Materials comply with project",
        "test_results": "Test protocol 15",
        "geometric_parameters": "Elevation matches project",
    }

    result = generator.save_act_data(
        project_name,
        act_code,
        act_data,
    )

    storage_path = (
        project_path / "hidden_works_act_data.json"
    )

    assert storage_path.is_file()

    loaded = generator.load_act_data(
        project_name,
        act_code,
    )

    assert loaded["act_number"] == "А-001"
    assert (
        loaded["compliance"]
        == "Работы соответствуют проектной документации"
    )
    assert loaded["next_works"] == "Обратная засыпка"
    assert loaded["remarks"] == "Замечаний нет"
    assert (
        loaded["attachments"]
        == "Исполнительная схема ИС-01"
    )

    assert (
        loaded["materials_compliance"]
        == "Materials comply with project"
    )
    assert loaded["test_results"] == "Test protocol 15"
    assert (
        loaded["geometric_parameters"]
        == "Elevation matches project"
    )

    assert set(result["saved_fields"]) >= {
        "act_number",
        "compliance",
        "next_works",
        "remarks",
        "attachments",
        "materials_compliance",
        "test_results",
        "geometric_parameters",
    }
