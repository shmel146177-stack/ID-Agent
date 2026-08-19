import io
import os

import fitz
import pytesseract

from PIL import Image


class OCRService:

    def __init__(self):

        self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        if os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def _detect_rotation(
        self,
        image: Image.Image,
    ) -> int:

        try:

            osd = pytesseract.image_to_osd(
                image,
                config="--psm 0",
                output_type=pytesseract.Output.DICT,
            )

            rotate = int(
                osd.get(
                    "rotate",
                    0,
                )
                or 0
            )

            if rotate not in {
                0,
                90,
                180,
                270,
            }:
                return 0

            return rotate

        except Exception:

            # Если ориентацию определить не удалось,
            # распознаём страницу без поворота.
            return 0

    def _rotate_image(
        self,
        image: Image.Image,
        rotate: int,
    ) -> Image.Image:

        if rotate == 0:
            return image

        # Tesseract OSD возвращает угол,
        # на который изображение надо повернуть
        # по часовой стрелке.
        #
        # PIL использует положительный угол
        # против часовой стрелки,
        # поэтому ставим минус.
        return image.rotate(
            -rotate,
            expand=True,
        )

    def _page_to_image(
        self,
        page,
        dpi: int = 300,
    ) -> Image.Image:
        """Преобразует страницу PDF в изображение для OCR."""

        zoom = dpi / 72

        matrix = fitz.Matrix(
            zoom,
            zoom,
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image_bytes = pixmap.tobytes("png")

        return Image.open(io.BytesIO(image_bytes))

    def recognize_page(
        self,
        file_path: str,
        page_number: int,
        language: str = "rus+eng",
        dpi: int = 300,
    ) -> dict:
        """
        OCR одной страницы PDF.

        page_number начинается с 1.
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        if not file_path.lower().endswith(".pdf"):
            raise ValueError("OCR пока поддерживает только PDF")

        document = fitz.open(file_path)

        try:

            if page_number < 1 or page_number > len(document):
                raise ValueError(
                    f"Страница вне диапазона: {page_number}. "
                    f"Всего страниц: {len(document)}"
                )

            page = document[page_number - 1]

            image = self._page_to_image(
                page,
                dpi=dpi,
            )

            try:

                # -------------------------------------
                # 1. ОПРЕДЕЛЯЕМ ОРИЕНТАЦИЮ
                # -------------------------------------

                rotation = self._detect_rotation(image)

                # -------------------------------------
                # 2. ИСПРАВЛЯЕМ ПОВОРОТ
                # -------------------------------------

                corrected_image = self._rotate_image(
                    image,
                    rotation,
                )

                try:

                    # ---------------------------------
                    # 3. OCR
                    # ---------------------------------

                    text = pytesseract.image_to_string(
                        corrected_image,
                        lang=language,
                        config="--psm 6",
                    )

                finally:

                    if corrected_image is not image:
                        corrected_image.close()

            finally:

                image.close()

            text = (text or "").strip()

            return {
                "file": os.path.basename(file_path),
                "page": page_number,
                "rotation": rotation,
                "text": text,
                "text_length": len(text),
                "ocr": True,
                "language": language,
            }

        finally:

            document.close()

    def recognize_page_region(
        self,
        file_path: str,
        page_number: int,
        region: tuple[float, float, float, float],
        language: str = "rus",
        dpi: int = 300,
        psm: int = 4,
    ) -> dict:
        """OCR прямоугольной области страницы в относительных координатах."""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        if not file_path.lower().endswith(".pdf"):
            raise ValueError("OCR пока поддерживает только PDF")

        left, top, right, bottom = region

        if not (
            0 <= left < right <= 1
            and 0 <= top < bottom <= 1
        ):
            raise ValueError("Область OCR должна находиться в пределах страницы")

        document = fitz.open(file_path)

        try:

            if page_number < 1 or page_number > len(document):
                raise ValueError(
                    f"Страница вне диапазона: {page_number}. "
                    f"Всего страниц: {len(document)}"
                )

            image = self._page_to_image(
                document[page_number - 1],
                dpi=dpi,
            )

            try:

                rotation = self._detect_rotation(image)

                corrected_image = self._rotate_image(
                    image,
                    rotation,
                )

                try:

                    width, height = corrected_image.size

                    region_image = corrected_image.crop(
                        (
                            round(width * left),
                            round(height * top),
                            round(width * right),
                            round(height * bottom),
                        )
                    )

                    try:

                        text = pytesseract.image_to_string(
                            region_image,
                            lang=language,
                            config=f"--psm {psm}",
                        )

                    finally:
                        region_image.close()

                finally:

                    if corrected_image is not image:
                        corrected_image.close()

            finally:
                image.close()

            text = (text or "").strip()

            return {
                "file": os.path.basename(file_path),
                "page": page_number,
                "rotation": rotation,
                "region": region,
                "text": text,
                "text_length": len(text),
                "ocr": True,
                "language": language,
                "psm": psm,
            }

        finally:
            document.close()

    def recognize_pdf(
        self,
        file_path: str,
        language: str = "rus+eng",
        dpi: int = 300,
    ) -> dict:

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        if not file_path.lower().endswith(".pdf"):
            raise ValueError("OCR пока поддерживает только PDF")

        document = fitz.open(file_path)

        pages = []
        full_text = []

        try:

            for page_number, page in enumerate(
                document,
                start=1,
            ):

                image = self._page_to_image(
                    page,
                    dpi=dpi,
                )

                try:

                    # ---------------------------------
                    # 1. ОПРЕДЕЛЯЕМ ОРИЕНТАЦИЮ
                    # ---------------------------------

                    rotation = self._detect_rotation(image)

                    # ---------------------------------
                    # 2. ИСПРАВЛЯЕМ ПОВОРОТ
                    # ---------------------------------

                    corrected_image = self._rotate_image(
                        image,
                        rotation,
                    )

                    try:

                        # -----------------------------
                        # 3. OCR
                        # -----------------------------

                        text = pytesseract.image_to_string(
                            corrected_image,
                            lang=language,
                            config="--psm 6",
                        )

                    finally:

                        if corrected_image is not image:
                            corrected_image.close()

                finally:

                    image.close()

                text = (text or "").strip()

                pages.append(
                    {
                        "page": page_number,
                        "rotation": rotation,
                        "text": text,
                        "text_length": len(text),
                    }
                )

                if text:
                    full_text.append(text)

        finally:

            document.close()

        combined_text = "\n\n".join(full_text)

        return {
            "file": os.path.basename(file_path),
            "pages_count": len(pages),
            "text_length": len(combined_text),
            "text": combined_text,
            "pages": pages,
            "ocr": True,
            "language": language,
        }


ocr_service = OCRService()
