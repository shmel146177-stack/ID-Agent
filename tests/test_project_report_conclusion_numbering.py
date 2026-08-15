from docx import Document

from app.generators.project_report_generator import ProjectReportGenerator


def test_project_report_conclusion_is_section_seven():
    generator = ProjectReportGenerator()
    document = Document()

    generator._add_conclusion(
        document,
        {},
    )

    full_text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    assert "7. Заключение ID-Agent" in full_text
