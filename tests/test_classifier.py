from pathlib import Path

from app.scanner.scanner import DocumentScanner
from app.analyzer.document_classifier import DocumentClassifier


def test_classifier_detects_document_type():
    pdf_path = next(
        Path("uploads").glob("*17.08.23 (1).pdf")
    )

    scanner = DocumentScanner()
    document = scanner.scan(str(pdf_path))

    classifier = DocumentClassifier()
    result = classifier.classify(document)

    assert result.filename
    assert result.pages == 10
    assert len(result.text) > 10000
    assert result.document_type == "Схема"
