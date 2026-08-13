import app.services.document_service as service_module
from app.services.document_service import DocumentService


def test_document_service_analyzes_pdf(monkeypatch, tmp_path):

    service = DocumentService()

    pdf_path = tmp_path / "test_document.pdf"

    pdf_path.write_bytes(
        b"FAKE PDF CONTENT"
    )

    extracted_text = (
        "Тестовый текст PDF. "
        "Шкаф управления. "
        "Номер чертежа TEST-001."
    )

    monkeypatch.setattr(
        service_module.pdf_parser,
        "extract_text",
        lambda file_path: extracted_text,
    )

    result = service.analyze(
        str(pdf_path)
    )

    assert result["filename"] == "test_document.pdf"
    assert result["extension"] == ".pdf"

    assert result["size_bytes"] == len(
        b"FAKE PDF CONTENT"
    )

    assert result["pages_text_length"] == len(
        extracted_text
    )

    assert result["preview"] == extracted_text[:500]

    assert "status" in result
