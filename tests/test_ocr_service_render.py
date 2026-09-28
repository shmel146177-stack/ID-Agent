import fitz

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
