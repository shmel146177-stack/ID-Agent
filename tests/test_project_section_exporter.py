import json
from pathlib import Path

from app.services.project_section_exporter import ProjectSectionExporter


def test_project_section_exporter_builds_export_summary(monkeypatch, tmp_path):

    exporter = ProjectSectionExporter()

    project_name = "TEST_PROJECT"

    project_path = tmp_path / project_name
    analysis_path = project_path / "analysis"
    source_folder = project_path / "source_docs"
    working_folder = project_path / "working_docs"

    project_path.mkdir(parents=True)

    page_analysis = {
        "documents": [
            {
                "filename": "project.pdf",
                "pages": [],
            }
        ]
    }

    groups = {
        "source_pages": [
            {
                "filename": "project.pdf",
                "page_number": 1,
            },
            {
                "filename": "project.pdf",
                "page_number": 2,
            },
        ],
        "working_pages": [
            {
                "filename": "project.pdf",
                "page_number": 3,
            }
        ],
        "unclassified_pages": [
            {
                "filename": "project.pdf",
                "page_number": 4,
            }
        ],
    }

    monkeypatch.setattr(
        exporter,
        "_project_path",
        lambda name: project_path,
    )

    monkeypatch.setattr(
        exporter,
        "_analysis_path",
        lambda name: analysis_path,
    )

    monkeypatch.setattr(
        exporter,
        "_source_folder",
        lambda name: source_folder,
    )

    monkeypatch.setattr(
        exporter,
        "_working_folder",
        lambda name: working_folder,
    )

    monkeypatch.setattr(
        exporter,
        "_load_json",
        lambda path: page_analysis,
    )

    monkeypatch.setattr(
        exporter,
        "_collect_pages",
        lambda data: groups,
    )

    export_calls = []

    def fake_export_group(
        project_name_value,
        page_analysis_value,
        pages,
        output_file,
    ):

        export_calls.append(
            {
                "project": project_name_value,
                "pages": list(pages),
                "output_file": Path(output_file),
            }
        )

        return {
            "file": str(output_file),
            "pages_count": len(pages),
            "pages": list(pages),
        }

    monkeypatch.setattr(
        exporter,
        "_export_group",
        fake_export_group,
    )

    result = exporter.export_project(project_name)

    assert result["project"] == project_name

    assert result["source_documents"]["pages_count"] == 2
    assert result["working_drawings"]["pages_count"] == 1

    assert result["unclassified_pages_count"] == 1
    assert len(result["unclassified_pages"]) == 1

    assert result["total_exported_pages"] == 3

    assert len(export_calls) == 2

    assert len(export_calls[0]["pages"]) == 2
    assert len(export_calls[1]["pages"]) == 1

    assert export_calls[0]["project"] == project_name
    assert export_calls[1]["project"] == project_name

    result_file = Path(result["analysis_file"])

    assert result_file.exists()
    assert result_file.name == "project_section_export.json"

    saved = json.loads(
        result_file.read_text(
            encoding="utf-8",
        )
    )

    assert saved["project"] == project_name
    assert saved["source_documents"]["pages_count"] == 2
    assert saved["working_drawings"]["pages_count"] == 1
    assert saved["unclassified_pages_count"] == 1
    assert saved["total_exported_pages"] == 3
