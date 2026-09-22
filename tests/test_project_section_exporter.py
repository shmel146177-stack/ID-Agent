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

    assert result["total_exported_pages"] == 4

    assert len(export_calls) == 3

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
    assert saved["total_exported_pages"] == 4


def test_real_pdf_export_preserves_unknown_pages_and_cleans_stale_review(tmp_path, monkeypatch):
    import fitz

    monkeypatch.chdir(tmp_path)
    root = tmp_path / "projects" / "sample"
    (root / "input").mkdir(parents=True)
    (root / "analysis").mkdir()
    original = root / "input" / "sample.pdf"
    with fitz.open() as document:
        for number in range(1, 5):
            document.new_page().insert_text((40, 40), f"Source page {number}")
        document.save(original)
    original_bytes = original.read_bytes()
    analysis = {"documents": [{"filename": "sample.pdf", "pages": [
        {"page": 1, "page_type": "Титульный лист"},
        {"page": 2, "page_type": "Рабочий чертеж"},
        {"page": 3, "page_type": "Не определено"},
        {"page": 4, "page_type": "Общие данные"},
    ]}]}
    analysis_file = root / "analysis" / "page_analysis.json"
    analysis_file.write_text(json.dumps(analysis), encoding="utf-8")
    exporter = ProjectSectionExporter()
    result = exporter.export_project("sample")
    assert result["total_exported_pages"] == 4
    assert result["requires_review"] is True
    seen = []
    for key in ("source_documents", "working_drawings", "review_documents"):
        group = result[key]
        with fitz.open(group["file"]) as document:
            assert len(document) == group["pages_count"]
            for page, mapping in zip(document, group["pages"], strict=True):
                number = mapping["source_page"]
                assert f"Source page {number}" in page.get_text()
                seen.append(number)
    assert sorted(seen) == [1, 2, 3, 4]
    assert original.read_bytes() == original_bytes
    review_file = Path(result["review_documents"]["file"])
    analysis["documents"][0]["pages"][2]["page_type"] = "Рабочий чертеж"
    analysis_file.write_text(json.dumps(analysis), encoding="utf-8")
    result = exporter.export_project("sample")
    assert not result["requires_review"]
    assert result["total_exported_pages"] == 4
    assert not review_file.exists()
