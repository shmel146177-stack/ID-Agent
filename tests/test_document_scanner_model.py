import pytest

from app.scanner.scanner import DocumentScanner


def test_document_scanner_pdf_and_missing_file(
    monkeypatch,
    tmp_path,
):

    scanner = DocumentScanner()

    pdf_file = tmp_path / "TEST.PDF"
    pdf_file.write_bytes(b"FAKE PDF")

    monkeypatch.setattr(
        scanner.pdf,
        "read",
        lambda file_path: {
            "pages": 3,
            "text": "Тестовый текст PDF",
        },
    )

    model = scanner.scan(
        str(pdf_file)
    )

    assert model.filename == "TEST.PDF"
    assert model.extension == ".pdf"
    assert model.pages == 3
    assert model.text == "Тестовый текст PDF"

    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        scanner.scan(
            str(missing_file)
        )
