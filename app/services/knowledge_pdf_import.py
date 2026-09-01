from pathlib import Path

from app.models.knowledge import KnowledgeChunk
from app.parsers.pdf_parser import PDFParser, pdf_parser
from app.services.knowledge_service import KnowledgeService


class KnowledgePDFImporter:
    def __init__(self, parser: PDFParser | None = None):
        self.parser = parser if parser is not None else pdf_parser

    def import_file(
        self,
        file_path: str | Path,
        source_id: str,
        source_title: str,
        service: KnowledgeService,
    ) -> list[KnowledgeChunk]:
        page_texts = self.parser.extract_pages(str(file_path))
        chunks = []

        for page_number, page_text in enumerate(
            page_texts,
            start=1,
        ):
            normalized_text = page_text.strip()

            if not normalized_text:
                continue

            chunk = KnowledgeChunk(
                source_id=source_id,
                source_title=source_title,
                page=page_number,
                text=normalized_text,
            )
            service.add(chunk)
            chunks.append(chunk)

        return chunks
