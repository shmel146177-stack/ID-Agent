import json
from pathlib import Path

from app.services.project_manager import ProjectManager


def test_project_manager_list_projects(tmp_path):

    manager = ProjectManager()
    manager.projects_root = str(tmp_path)

    # ---------------------------------------------------------
    # Проект A
    # ---------------------------------------------------------

    project_a = tmp_path / "A_PROJECT"

    (project_a / "input").mkdir(parents=True)
    (project_a / "output").mkdir()
    (project_a / "executive_docs").mkdir()

    (project_a / "project.json").write_text(
        json.dumps(
            {
                "project_name": "A_PROJECT",
                "object_name": "Объект A",
                "address": "Москва",
                "customer": "Заказчик A",
                "contractor": "Подрядчик A",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (project_a / "input" / "one.pdf").write_bytes(b"1")
    (project_a / "input" / "two.pdf").write_bytes(b"2")

    (project_a / "output" / "report.docx").write_bytes(b"3")

    (project_a / "executive_docs" / "registry.xlsx").write_bytes(b"4")

    # Вложенная папка не должна считаться файлом.
    (project_a / "input" / "nested").mkdir()

    # ---------------------------------------------------------
    # Проект B
    # ---------------------------------------------------------

    project_b = tmp_path / "B_PROJECT"

    (project_b / "input").mkdir(parents=True)

    (project_b / "project.json").write_text(
        json.dumps(
            {
                "project_name": "",
                "object_name": "Объект B",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (project_b / "input" / "drawing.pdf").write_bytes(b"5")

    # ---------------------------------------------------------
    # Папка без project.json — должна быть пропущена
    # ---------------------------------------------------------

    (tmp_path / "NO_PROJECT_JSON").mkdir()

    # ---------------------------------------------------------
    # Битый project.json — должен быть пропущен
    # ---------------------------------------------------------

    broken = tmp_path / "BROKEN_PROJECT"
    broken.mkdir()

    (broken / "project.json").write_text(
        "{broken json",
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Проверка
    # ---------------------------------------------------------

    result = manager.list_projects()

    assert len(result) == 2

    assert result[0]["project_name"] == "A_PROJECT"
    assert result[1]["project_name"] == "B_PROJECT"

    assert result[0]["object_name"] == "Объект A"
    assert result[0]["address"] == "Москва"
    assert result[0]["customer"] == "Заказчик A"
    assert result[0]["contractor"] == "Подрядчик A"

    assert result[0]["input_files"] == 2
    assert result[0]["output_files"] == 1
    assert result[0]["executive_files"] == 1

    assert result[1]["object_name"] == "Объект B"
    assert result[1]["input_files"] == 1
    assert result[1]["output_files"] == 0
    assert result[1]["executive_files"] == 0
