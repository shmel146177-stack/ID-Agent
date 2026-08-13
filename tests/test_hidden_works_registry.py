import json

from app.services.hidden_works_registry import HiddenWorksRegistry


def test_hidden_works_registry_detects_act(monkeypatch, tmp_path):

    registry = HiddenWorksRegistry()

    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"

    project_path.mkdir(parents=True)

    rule = registry.RULES[0]

    monkeypatch.setattr(
        registry,
        "_project_path",
        lambda project_name: project_path,
    )

    monkeypatch.setattr(
        registry,
        "_analysis_path",
        lambda project_name: analysis_path,
    )

    monkeypatch.setattr(
        registry,
        "_extract_register_entries",
        lambda project_name: [],
    )

    monkeypatch.setattr(
        registry,
        "_load_page_types",
        lambda project_name: {
            rule["page_types"][0]: 1,
        },
    )

    result = registry.analyze_project(
        "TEST_PROJECT"
    )

    assert result["project"] == "TEST_PROJECT"
    assert result["acts_count"] == 1
    assert result["requires_field_confirmation"] is True

    act = result["acts"][0]

    assert act["code"] == rule["code"]
    assert act["title"] == rule["title"]
    assert act["act_title"] == rule["act_title"]
    assert act["confirmation_required"] is True
    assert len(act["evidence"]) == 1

    output_path = analysis_path / "hidden_works_registry.json"

    assert output_path.exists()
    assert result["analysis_file"] == str(output_path)

    saved = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved["acts_count"] == 1
    assert saved["acts"][0]["code"] == rule["code"]
