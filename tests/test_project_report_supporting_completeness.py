from docx import Document

from app.generators.project_report_generator import ProjectReportGenerator


def test_report_supporting_documents_shows_completeness_counts():
    generator = ProjectReportGenerator()
    document = Document()

    supporting_documents = {
        "requirements_count": 2,
        "high_priority_count": 1,
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0441\u0445\u0435\u043c\u044b",
                "required_count": 2,
                "found_count": 1,
                "missing_count": 1,
                "documents": [],
            },
        ],
    }

    generator._add_supporting_documents(
        document,
        supporting_documents,
    )

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    assert "\u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f: 2" in text
    assert "\u043d\u0430\u0439\u0434\u0435\u043d\u043e: 1" in text
    assert "\u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442: 1" in text
