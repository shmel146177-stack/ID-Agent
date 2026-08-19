import json
from pathlib import Path

from app.services.project_manager import ProjectManager


def test_project_manager_create_get_update(monkeypatch, tmp_path):

    manager = ProjectManager()

    manager.projects_root = str(tmp_path)

    project_name = "TEST_PROJECT"

    created = manager.create_project(project_name)

    project_path = Path(tmp_path) / project_name
    project_file = project_path / "project.json"

    assert project_path.exists()
    assert project_file.exists()

    assert created["project_name"] == project_name
    assert created["project_mode"] == "production"

    saved = json.loads(
        project_file.read_text(
            encoding="utf-8",
        )
    )

    assert saved["project_name"] == project_name

    loaded = manager.get_project(project_name)

    assert loaded["project_name"] == project_name

    updated = manager.update_project(
        project_name,
        {
            "object_name": "ТП-101",
            "address": "Москва",
            "customer": "ООО Заказчик",
            "project_mode": "training",
            "project_note": "Учебный архивный проект",
            "forbidden_field": "НЕ ДОЛЖНО СОХРАНИТЬСЯ",
            "project_name": "OTHER_PROJECT",
        },
    )

    assert updated["project_name"] == project_name
    assert updated["object_name"] == "ТП-101"
    assert updated["address"] == "Москва"
    assert updated["customer"] == "ООО Заказчик"
    assert updated["project_mode"] == "training"
    assert updated["project_note"] == "Учебный архивный проект"

    assert "forbidden_field" not in updated

    loaded_again = manager.get_project(project_name)

    assert loaded_again == updated
    assert loaded_again["project_name"] == project_name
    assert "forbidden_field" not in loaded_again


def test_project_manager_rejects_unknown_project_mode(monkeypatch, tmp_path):

    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    manager.create_project("TEST_PROJECT")

    try:
        manager.update_project(
            "TEST_PROJECT",
            {"project_mode": "unknown"},
        )
    except ValueError as error:
        assert "production или training" in str(error)
    else:
        raise AssertionError("Ожидалась ошибка режима проекта")
