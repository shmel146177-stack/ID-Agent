import fitz

import app.services.ocr_service as ocr_module
from app.services.ocr_service import OCRService


def test_page_to_image_keeps_rendered_pixels():
    with fitz.open() as document:
        page = document.new_page(width=72, height=72)
        page.draw_rect(
            fitz.Rect(12, 12, 60, 60),
            color=(1, 0, 0),
            fill=(1, 0, 0),
        )

        image = OCRService()._page_to_image(page, dpi=72)
        try:
            assert image.mode == "RGB"
            assert image.size == (72, 72)
            assert image.getpixel((36, 36)) == (255, 0, 0)
            assert image.getpixel((0, 0)) == (255, 255, 255)
        finally:
            image.close()


def test_ocr_reuses_unchanged_page_only_within_run(monkeypatch, tmp_path):
    pdf_path = tmp_path / "scan.pdf"

    def write_pdf(color):
        with fitz.open() as document:
            page = document.new_page(width=72, height=72)
            page.draw_rect(fitz.Rect(10, 10, 60, 60), fill=color)
            document.save(pdf_path)

    write_pdf((1, 0, 0))
    service = OCRService()
    monkeypatch.setattr(service, "_detect_rotation", lambda image: 0)
    calls = []

    def recognize(image, **kwargs):
        calls.append(kwargs["config"])
        return "recognized text"

    monkeypatch.setattr(ocr_module.pytesseract, "image_to_string", recognize)

    with service.reuse_pages_within_run():
        whole = service.recognize_pdf(str(pdf_path))
        page = service.recognize_page(str(pdf_path), 1)
        assert page["text"] == whole["pages"][0]["text"]
        assert calls == ["--psm 6"]

        service.recognize_page(str(pdf_path), 1, psm=4)
        assert calls == ["--psm 6", "--psm 4"]

        write_pdf((0, 1, 0))
        service.recognize_page(str(pdf_path), 1)
        assert calls == ["--psm 6", "--psm 4", "--psm 6"]

    service.recognize_page(str(pdf_path), 1)
    assert len(calls) == 4

    monkeypatch.setattr(service, "_source_digest", lambda path: None)
    with service.reuse_pages_within_run():
        service.recognize_pdf(str(pdf_path))
        service.recognize_page(str(pdf_path), 1)
    assert len(calls) == 6
