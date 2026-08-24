from pathlib import Path

import pytest

from app.services.page_analysis_service import PageAnalysisService


def test_page_analysis_uses_ocr_for_scanned_page():

    pdf_files = list(
        Path("projects/ТП-103/input").glob("kyoScan*.pdf")
    )

    if not pdf_files:
        pytest.skip("Local OCR integration PDF is not available")

    pdf_path = pdf_files[0]

    result = PageAnalysisService().analyze_pdf(
        pdf_path
    )

    assert result["filename"] == pdf_path.name
    assert result["pages_count"] == 1

    assert result["text_pages_count"] == 0
    assert result["ocr_pages_count"] == 1

    assert len(result["pages"]) == 1

    page = result["pages"][0]

    assert page["page"] == 1
    assert page["source"] == "ocr"
    assert page["ocr_used"] is True
    assert page["rotation"] == 90
    assert page["text_length"] > 1500

    assert page["page_type"] is not None
    assert isinstance(result["page_types"], dict)
    assert len(result["page_types"]) >= 1
