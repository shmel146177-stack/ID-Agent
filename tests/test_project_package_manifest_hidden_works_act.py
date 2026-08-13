import json
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_manifest_contains_generated_hidden_works_act(
    tmp_path,
):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    destination_folder = tmp_path / "executive_docs"

    acts_folder = (
        destination_folder
        / "Исполнительная_документация"
        / "03_Акты_скрытых_работ"
    )

    acts_folder.mkdir(
        parents=True,
    )

    act_file = (
        acts_folder
        / "АОСР_Заземление_TEST_PROJECT.docx"
    )

    act_file.write_bytes(
        b"HIDDEN WORKS ACT"
    )

    processor_result = {
        "status": "Готово",
        "completeness": {},
        "hidden_works_acts": {
            "acts_detected": 1,
            "acts_created": 1,
            "acts_skipped": 0,
            "requires_field_confirmation": True,
            "created": [
                {
                    "code": "grounding_device",
                    "title": "АОСР на устройство заземления",
                    "priority": "Высокий",
                    "file": str(act_file),
                }
            ],
        },
        "hidden_works_journal": None,
    }

    document_set_result = {
        "sections_count": 0,
        "sections_with_files": 0,
        "actual_files_count": 0,
        "sections": [],
    }

    inventory = {
        "files": [],
        "folders": [],
    }

    manifest_path = package._create_manifest(
        project_name,
        destination_folder,
        processor_result,
        document_set_result,
        inventory,
        [],
    )

    manifest = json.loads(
        Path(manifest_path).read_text(
            encoding="utf-8",
        )
    )

    hidden_works = manifest[
        "hidden_works_acts"
    ]

    assert hidden_works["acts_detected"] == 1
    assert hidden_works["acts_created"] == 1
    assert hidden_works["acts_skipped"] == 0
    assert (
        hidden_works["requires_field_confirmation"]
        is True
    )

    assert len(
        hidden_works["created"]
    ) == 1

    act = hidden_works[
        "created"
    ][0]

    expected_path = (
        "Исполнительная_документация/"
        "03_Акты_скрытых_работ/"
        "АОСР_Заземление_TEST_PROJECT.docx"
    )

    assert act["code"] == "grounding_device"
    assert act["title"] == "АОСР на устройство заземления"
    assert act["priority"] == "Высокий"
    assert act["file"] == expected_path
