import json
from pathlib import Path

from app.services.project_package import ProjectPackage


def test_project_package_manifest_contains_hidden_works_journal(
    tmp_path,
):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    destination_folder = tmp_path / "executive_docs"

    journal_folder = (
        destination_folder
        / "Исполнительная_документация"
        / "07_Журналы_работ"
    )

    journal_folder.mkdir(
        parents=True,
    )

    journal_file = (
        journal_folder
        / "Журнал_скрытых_работ_TEST_PROJECT.docx"
    )

    journal_file.write_bytes(
        b"JOURNAL"
    )

    processor_result = {
        "status": "Готово",
        "completeness": {},
        "hidden_works_acts": {
            "acts_detected": 0,
            "acts_created": 0,
            "acts_skipped": 0,
        },
        "hidden_works_journal": str(journal_file),
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

    journal = manifest[
        "hidden_works_journal"
    ]

    expected_path = (
        "Исполнительная_документация"
        "/07_Журналы_работ/"
        "Журнал_скрытых_работ_TEST_PROJECT.docx"
    )

    assert journal["file"] == expected_path
    assert journal["exists"] is True
    assert journal["size_bytes"] > 0

    assert (
        manifest["generated_documents"][
            "hidden_works_journal"
        ]
        == expected_path
    )
