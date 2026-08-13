import app.generators.hidden_works_act_generator as generator_module
from app.generators.hidden_works_act_generator import HiddenWorksActGenerator


def test_hidden_works_act_generator_create_all(monkeypatch):

    generator = HiddenWorksActGenerator()

    supported_code = next(
        iter(generator.ACT_CONFIG)
    )

    registry = {
        "acts_count": 2,
        "requires_field_confirmation": True,
        "acts": [
            {
                "code": supported_code,
                "act_title": "Тестовый АОСР",
                "priority": "Высокий",
            },
            {
                "code": "__unsupported_act__",
                "act_title": "Неподдерживаемый АОСР",
                "priority": "Средний",
            },
        ],
    }

    monkeypatch.setattr(
        generator_module.hidden_works_registry,
        "analyze_project",
        lambda project_name: registry,
    )

    saved_data = {
        "act_number": "А-001",
    }

    monkeypatch.setattr(
        generator,
        "load_act_data",
        lambda project_name, act_code: saved_data,
    )

    calls = []

    def fake_create(
        project_name,
        act_code,
        registry=None,
        act_data=None,
    ):
        calls.append(
            {
                "project_name": project_name,
                "act_code": act_code,
                "registry": registry,
                "act_data": act_data,
            }
        )

        return "test_act.docx"

    monkeypatch.setattr(
        generator,
        "create",
        fake_create,
    )

    result = generator.create_all(
        "TEST_PROJECT"
    )

    assert result["project"] == "TEST_PROJECT"
    assert result["acts_detected"] == 2
    assert result["acts_created"] == 1
    assert result["acts_skipped"] == 1
    assert result["requires_field_confirmation"] is True

    assert len(result["created"]) == 1
    assert result["created"][0]["code"] == supported_code
    assert result["created"][0]["file"] == "test_act.docx"

    assert len(result["skipped"]) == 1
    assert (
        result["skipped"][0]["code"]
        == "__unsupported_act__"
    )

    assert len(calls) == 1
    assert calls[0]["project_name"] == "TEST_PROJECT"
    assert calls[0]["act_code"] == supported_code
    assert calls[0]["registry"] is registry
    assert calls[0]["act_data"] == saved_data
