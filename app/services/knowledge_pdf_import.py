from pathlib import Path

from app.models.knowledge import KnowledgeChunk
from app.parsers.pdf_parser import PDFParser, pdf_parser
from app.services.knowledge_service import KnowledgeService
from app.services.ocr_service import OCRService


class KnowledgePDFImporter:
    def __init__(
        self,
        parser: PDFParser | None = None,
        ocr_service: OCRService | None = None,
    ):
        self.parser = parser if parser is not None else pdf_parser
        self.ocr_service = ocr_service

    def import_file(
        self,
        file_path: str | Path,
        source_id: str,
        source_title: str,
        service: KnowledgeService,
        ocr_empty_pages: bool = False,
        ocr_dpi: int = 150,
        ocr_psm: int = 6,
        page_numbers: set[int] | None = None,
        replace_existing_pages: bool = False,
    ) -> list[KnowledgeChunk]:
        if ocr_empty_pages and ocr_dpi <= 0:
            raise ValueError("ocr_dpi must be positive")

        if ocr_empty_pages and not 1 <= ocr_psm <= 13:
            raise ValueError(
                "ocr_psm must be between 1 and 13"
            )

        if page_numbers is not None and any(
            page_number <= 0
            for page_number in page_numbers
        ):
            raise ValueError(
                "page_numbers must contain positive values"
            )

        page_texts = self.parser.extract_pages(str(file_path))
        chunks = []

        for page_number, page_text in enumerate(
            page_texts,
            start=1,
        ):
            if (
                page_numbers is not None
                and page_number not in page_numbers
            ):
                continue

            normalized_text = page_text.strip()
            text_origin = "native"
            requires_human_review = False

            if not normalized_text and ocr_empty_pages:
                if self.ocr_service is None:
                    self.ocr_service = OCRService()

                ocr_result = self.ocr_service.recognize_page(
                    str(file_path),
                    page_number,
                    dpi=ocr_dpi,
                    psm=ocr_psm,
                )
                normalized_text = (
                    ocr_result.get("text") or ""
                ).strip()

                if normalized_text:
                    text_origin = "ocr"
                    requires_human_review = True

            if not normalized_text:
                continue

            chunk = KnowledgeChunk(
                source_id=source_id,
                source_title=source_title,
                page=page_number,
                text_origin=text_origin,
                requires_human_review=requires_human_review,
                text=normalized_text,
            )
            if replace_existing_pages:
                service.upsert(chunk)
            else:
                service.add(chunk)

            chunks.append(chunk)

        return chunks
