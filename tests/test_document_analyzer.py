from pathlib import Path

import pytest

from app.scanner.scanner import DocumentScanner
from app.services.document_analyzer import DocumentAnalyzer


def test_document_analyzer_extracts_equipment_data():
    pdf_files = list(
        Path("uploads").glob("*17.08.23 (1).pdf")
    )

    if not pdf_files:
        pytest.skip("Local integration PDF is not available")

    pdf_path = pdf_files[0]

    document = DocumentScanner().scan(str(pdf_path))
    result = DocumentAnalyzer().analyze_text(document.text)

    assert result["document_type"] == "Документация оборудования"
    assert result["manufacturer"] == 'ООО "Торговый Дом АДЛ"'
    assert result["equipment"] == 'Шкаф управления "Грантор" АЭП40-016-54К-22У, 7,5 кВт, Iном=(10 - 16) А'
    assert result["date"] == "17.08.2023"
    assert result["drawing_number"] == "ТДЭО.30182.АЭП40-016-54К-22У"
    assert result["power"] == "7,5 кВт"
    assert result["voltage"] == "24В"
    assert result["current"] == "10 - 16 А"
    assert result["ip"] == "IP66"
    assert result["frequency"] == "50 Гц"
    assert result["weight"] is None
    assert result["serial_number"] is None
