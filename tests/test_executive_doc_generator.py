from pathlib import Path

from docx import Document

from app.generators.executive_doc_generator import ExecutiveDocumentGenerator


def test_executive_doc_generator_creates_real_docx(monkeypatch, tmp_path):

    monkeypatch.chdir(tmp_path)

    generator = ExecutiveDocumentGenerator()

    data = {
        "equipment": "Шкаф управления TEST-001",
        "manufacturer": "ООО Тест",
        "date": "12.08.2026",
        "drawing_number": "TEST-DWG-001",
    }

    result = generator.create(data)

    output_path = Path(result)

    assert output_path.exists()
    assert output_path.is_file()
    assert output_path.suffix == ".docx"

    document = Document(output_path)

    all_text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    assert "ID-Agent" in all_text
    assert "Шкаф управления TEST-001" in all_text
    assert "ООО Тест" in all_text
    assert "12.08.2026" in all_text
    assert "TEST-DWG-001" in all_text
