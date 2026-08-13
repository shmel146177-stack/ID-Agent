from app.generators.hidden_works_act_generator import HiddenWorksActGenerator


def test_hidden_works_act_partial_update_preserves_existing_data(
    monkeypatch,
    tmp_path,
):

    monkeypatch.chdir(tmp_path)

    generator = HiddenWorksActGenerator()

    project_name = "TEST_PROJECT"
    act_code = "grounding_device"

    generator.save_act_data(
        project_name,
        act_code,
        {
            "act_number": "А-004",
            "compliance": "Соответствует проекту",
            "remarks": "Замечаний нет",
        },
    )

    generator.save_act_data(
        project_name,
        act_code,
        {
            "next_works": "Обратная засыпка",
            "compliance": "",
            "remarks": "",
        },
    )

    loaded = generator.load_act_data(
        project_name,
        act_code,
    )

    assert loaded["act_number"] == "А-004"
    assert loaded["compliance"] == "Соответствует проекту"
    assert loaded["remarks"] == "Замечаний нет"
    assert loaded["next_works"] == "Обратная засыпка"
