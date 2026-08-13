from pathlib import Path

from app.services.ocr_service import OCRService


def test_real_ocr_with_rotation():

    pdf_path = next(
        Path("projects/ТП-103/input").glob("kyoScan*.pdf")
    )

    result = OCRService().recognize_pdf(
        str(pdf_path)
    )

    assert result["ocr"] is True
    assert result["language"] == "rus+eng"

    assert result["pages_count"] == 1
    assert len(result["pages"]) == 1

    assert result["pages"][0]["rotation"] == 90

    assert result["text_length"] > 1500
    assert len(result["text"]) > 1500

    text_lower = result["text"].lower()

    assert "счет" in text_lower
    assert "фактур" in text_lower
    assert "продавец" in text_lower
    assert "покупатель" in text_lower
