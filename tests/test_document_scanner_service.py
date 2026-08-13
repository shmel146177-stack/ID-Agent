import app.services.document_scanner as scanner_module
from app.services.document_scanner import DocumentScanner


def test_document_scanner_uses_ocr_when_pdf_has_no_text(monkeypatch):

    monkeypatch.setattr(
        scanner_module.pdf_parser,
        "extract_text",
        lambda file_path: "",
    )

    monkeypatch.setattr(
        scanner_module.ocr_service,
        "recognize_pdf",
        lambda file_path: {
            "text": "Счет-фактура № 123 от 12.08.2026",
            "pages_count": 2,
            "language": "rus+eng",
        },
    )

    monkeypatch.setattr(
        scanner_module.document_analyzer,
        "analyze_text",
        lambda text: {
            "document_type": "Не определён",
            "date": "12.08.2026",
        },
    )

    monkeypatch.setattr(
        scanner_module.document_classifier,
        "classify",
        lambda filename, text: "Счет-фактура",
    )

    result = DocumentScanner().analyze_pdf(
        "test_scan.pdf"
    )

    assert result["filename"] == "test_scan.pdf"
    assert result["extension"] == ".pdf"

    assert result["ocr_used"] is True
    assert result["ocr"]["pages_count"] == 2
    assert result["ocr"]["language"] == "rus+eng"

    assert result["text_length"] > 0
    assert result["classification"] == "Счет-фактура"

    assert (
        result["analysis"]["document_type"]
        == "Счет-фактура"
    )

    assert (
        result["analysis"]["date"]
        == "12.08.2026"
    )
