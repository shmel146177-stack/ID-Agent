import app.services.project_package as package_module
from app.services.project_package import ProjectPackage


def test_project_package_create_builds_package_summary(monkeypatch, tmp_path):

    package = ProjectPackage()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    destination_folder = project_path / "executive_docs"

    project_path.mkdir(parents=True)

    processor_result = {
        "completeness": {
            "completeness_percent": 75.0,
            "missing_sheets": [
                {
                    "sheet_number": 4,
                    "title": "Недостающий лист",
                }
            ],
        },
        "hidden_works_acts": {
            "acts_detected": 2,
            "acts_created": 1,
            "acts_skipped": 1,
        },
        "hidden_works_journal": "journal.docx",
    }

    document_set_result = {
        "sections_count": 8,
        "sections_with_files": 3,
        "actual_files_count": 6,
    }

    final_documents = [
        "08/report.docx",
        "08/registry.xlsx",
    ]

    monkeypatch.setattr(
        package,
        "_project_path",
        lambda name: project_path,
    )

    monkeypatch.setattr(
        package,
        "_executive_docs_path",
        lambda name: destination_folder,
    )

    monkeypatch.setattr(
        package_module.project_processor,
        "process",
        lambda name: processor_result,
    )

    monkeypatch.setattr(
        package,
        "_sync_final_documents",
        lambda name, result: list(final_documents),
    )

    monkeypatch.setattr(
        package_module.project_document_set,
        "create",
        lambda name: document_set_result,
    )

    monkeypatch.setattr(
        package,
        "_copy_output_documents",
        lambda name, folder: [
            "report.docx",
            "registry.xlsx",
        ],
    )

    monkeypatch.setattr(
        package,
        "_copy_project_card",
        lambda name, folder: "project.json",
    )

    monkeypatch.setattr(
        package,
        "_copy_analysis_files",
        lambda name, folder: [
            "project_analysis.json",
            "document_registry.json",
        ],
    )

    inventory = {
        "files": [
            "report.docx",
            "registry.xlsx",
            "project.json",
            "project_analysis.json",
            "document_registry.json",
        ],
        "folders": [
            "01",
            "02",
            "08",
        ],
    }

    monkeypatch.setattr(
        package,
        "_inventory_package",
        lambda folder: inventory,
    )

    manifest_path = destination_folder / "package_manifest.json"

    def fake_create_manifest(
        project_name_value,
        destination,
        processor,
        document_set,
        inventory_value,
        final_documents_value,
    ):
        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        manifest_path.write_text(
            (
                "{\"status\": \"\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 "
                "\u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\"}"
            ),
            encoding="utf-8",
        )

        return str(manifest_path)

    monkeypatch.setattr(
        package,
        "_create_manifest",
        fake_create_manifest,
    )

    result = package.create(project_name)

    assert result["project"] == project_name
    assert result["status"] == (
        "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 "
        "\u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"
    )

    assert result["package_folder"] == str(destination_folder)

    assert result["files_count"] == 5
    assert result["folders_count"] == 3
    assert result["total_files_with_manifest"] == 6

    assert result["manifest"] == str(manifest_path)
    assert manifest_path.exists()

    assert result["completeness_percent"] == 75.0
    assert len(result["missing_sheets"]) == 1

    assert result["acts_detected"] == 2
    assert result["acts_created"] == 1
    assert result["acts_skipped"] == 1

    assert result["hidden_works_journal"] == "journal.docx"

    assert result["final_documents_copied"] == 2
    assert result["final_documents_files"] == final_documents

    assert result["document_sections"] == 8
    assert result["sections_with_files"] == 3
    assert result["section_files_count"] == 6

    assert result["copied_files"] == [
        "report.docx",
        "registry.xlsx",
        "project.json",
        "project_analysis.json",
        "document_registry.json",
    ]
