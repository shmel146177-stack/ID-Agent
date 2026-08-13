from pathlib import Path

from app.scanner.scanner import DocumentScanner


def test_scanner_reads_pdf():
    pdf_path = next(
        Path("uploads").glob("*17.08.23 (1).pdf")
    )

    scanner = DocumentScanner()
    doc = scanner.scan(str(pdf_path))

    assert doc.filename
    assert doc.extension.lower() == ".pdf"
    assert doc.pages == 10
    assert len(doc.text) > 10000
