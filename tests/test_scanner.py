from pathlib import Path

import pytest

from app.scanner.scanner import DocumentScanner


def test_scanner_reads_pdf():
    pdf_files = list(
        Path("uploads").glob("*17.08.23 (1).pdf")
    )

    if not pdf_files:
        pytest.skip("Local integration PDF is not available")

    pdf_path = pdf_files[0]

    scanner = DocumentScanner()
    doc = scanner.scan(str(pdf_path))

    assert doc.filename
    assert doc.extension.lower() == ".pdf"
    assert doc.pages == 10
    assert len(doc.text) > 10000
