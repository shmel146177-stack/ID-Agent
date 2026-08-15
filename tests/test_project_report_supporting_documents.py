from docx import Document

from app.generators.project_report_generator import ProjectReportGenerator


def test_project_report_adds_supporting_documents_section():
    generator = ProjectReportGenerator()
    document = Document()

    supporting_documents = {
        "requirements_count": 3,
        "high_priority_count": 2,
        "requires_field_confirmation": True,
        "sections": [
            {
                "number": "04",
                "title": "Исполнительные схемы",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "title": "Исполнительная схема заземляющего устройства",
                        "priority": "Высокий",
                    },
                ],
            },
            {
                "number": "05",
                "title": "Протоколы и испытания",
                "required_count": 1,
                "high_priority_count": 1,
                "documents": [
                    {
                        "title": "Протокол измерения сопротивления заземляющего устройства",
                        "priority": "Высокий",
                    },
                ],
            },
            {
                "number": "06",
                "title": "Паспорта и сертификаты",
                "required_count": 1,
                "high_priority_count": 0,
                "documents": [
                    {
                        "title": "Документы качества на материалы",
                        "priority": "Средний",
                    },
                ],
            },
        ],
    }

    generator._add_supporting_documents(
        document,
        supporting_documents,
    )

    full_text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    assert "Сопроводительная исполнительная документация" in full_text
    assert "Исполнительные схемы" in full_text
    assert "Протоколы и испытания" in full_text
    assert "Паспорта и сертификаты" in full_text
    assert "Исполнительная схема заземляющего устройства" in full_text
    assert "Протокол измерения сопротивления" in full_text
    assert "Документы качества на материалы" in full_text
