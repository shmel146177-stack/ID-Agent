from docx import Document
import pytest

from app.generators.project_document_set import ProjectDocumentSet
from app.generators.project_report_generator import ProjectReportGenerator
from app.services.project_package import ProjectPackage


@pytest.mark.parametrize(
    ("requirements", "filenames", "analysis", "expected"),
    [
        ([{"code": "a"}], ["unrelated.pdf"], False, (0, 1, 0, "Требует проверки")),
        (
            [{"code": "a"}, {"code": "b"}],
            ["unrelated.pdf"],
            False,
            (0, 1, 1, "Неполный комплект"),
        ),
        (
            [{"code": "a", "match_keywords": ["кабель"]}, {"code": "b"}],
            ["cable.pdf", "other.pdf"],
            True,
            (1, 1, 0, "Требует проверки"),
        ),
        (
            [{"code": "a", "match_keywords": ["кабель"]}],
            ["other.pdf"],
            True,
            (0, 0, 1, "Неполный комплект"),
        ),
        (
            [{"code": "a", "match_keywords": ["кабель"]}],
            ["other.pdf"],
            False,
            (0, 1, 0, "Требует проверки"),
        ),
        (
            [{"code": "a", "match_any_keywords": ["кабель"]}],
            ["cable.pdf"],
            True,
            (1, 0, 0, "Комплект сформирован"),
        ),
    ],
)
def test_supporting_section_separates_matches_review_and_missing(
    monkeypatch, tmp_path, requirements, filenames, analysis, expected
):
    document_set = ProjectDocumentSet()
    files = [{"name": filename} for filename in filenames]
    section_data = {
        "code": "executive_schemes",
        "required_count": len(requirements),
        "documents": requirements,
    }
    folder = {
        "number": "04",
        "code": "executive_schemes",
        "title": "Исполнительные схемы",
        "folder": "04_Исполнительные_схемы",
        "path": tmp_path,
        "description": "Исполнительные схемы",
    }

    monkeypatch.setattr(document_set, "_detected_documents", lambda name: {})
    monkeypatch.setattr(document_set, "_list_section_files", lambda path: files)
    monkeypatch.setattr(document_set, "_analysis_path", lambda name: tmp_path)

    def load_analysis(path):
        if not analysis:
            return {}
        if path.name == "project_analysis.json":
            return {
                "documents": [
                    {"filename": filename, "classification": "Схема"}
                    for filename in filenames
                ]
            }
        return {
            "documents": [
                {
                    "filename": filename,
                    "pages": [
                        {"text": "кабель" if filename == "cable.pdf" else "прочее"}
                    ],
                }
                for filename in filenames
            ]
        }

    monkeypatch.setattr(document_set, "_load_json", load_analysis)
    section = document_set._build_sections(
        "TEST_PROJECT", [folder], {}, {"sections": [section_data]}
    )[0]

    assert (
        section["detected"]["found_count"],
        section["detected"]["review_count"],
        section["detected"]["missing_count"],
        section["status"],
    ) == expected


def test_report_uses_same_review_count(monkeypatch, tmp_path):
    report = ProjectReportGenerator()
    monkeypatch.setattr(report, "_project_path", lambda name: tmp_path)
    monkeypatch.setattr(
        ProjectDocumentSet,
        "_list_section_files",
        lambda self, path: [{"name": "unknown.pdf"}],
    )

    result = report._with_supporting_completeness(
        "TEST_PROJECT",
        {
            "sections": [
                {
                    "code": "executive_schemes",
                    "number": "04",
                    "title": "Исполнительные схемы",
                    "required_count": 1,
                    "documents": [{"code": "scheme"}],
                }
            ]
        },
    )
    section = result["sections"][0]
    assert (
        section["found_count"],
        section["review_count"],
        section["missing_count"],
    ) == (
        0,
        1,
        0,
    )

    document = Document()
    report._add_supporting_documents(document, result)
    assert "требует проверки: 1" in " ".join(p.text for p in document.paragraphs)


def test_manifest_preserves_review_count(tmp_path):
    section = {
        "number": "04",
        "code": "executive_schemes",
        "title": "Исполнительные схемы",
        "status": "Требует проверки",
        "path": tmp_path,
        "detected": {
            "required_count": 1,
            "found_count": 0,
            "review_count": 1,
            "missing_count": 0,
        },
    }
    result = ProjectPackage()._build_document_sections(
        {"sections": [section]}, tmp_path
    )
    assert result[0]["status"] == "Требует проверки"
    assert result[0]["review_count"] == 1
