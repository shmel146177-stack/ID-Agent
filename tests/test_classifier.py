from pathlib import Path

import pytest

from app.scanner.scanner import DocumentScanner
from app.analyzer.document_classifier import DocumentClassifier


def test_classifier_detects_document_type():
    pdf_files = list(
        Path("uploads").glob("*17.08.23 (1).pdf")
    )

    if not pdf_files:
        pytest.skip("Local integration PDF is not available")

    pdf_path = pdf_files[0]

    scanner = DocumentScanner()
    document = scanner.scan(str(pdf_path))

    classifier = DocumentClassifier()
    result = classifier.classify(document)

    assert result.filename
    assert result.pages == 10
    assert len(result.text) > 10000
    assert result.document_type == "Схема"
