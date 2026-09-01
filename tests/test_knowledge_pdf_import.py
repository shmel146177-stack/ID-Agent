from app.models.knowledge import KnowledgeChunk
from app.services.knowledge_pdf_import import KnowledgePDFImporter
from app.services.knowledge_repository import KnowledgeRepository
from app.services.knowledge_service import KnowledgeService


class FakePDFParser:
    def extract_pages(self, file_path):
        assert file_path == "source.pdf"

        return [
            " First page requirement. ",
            "",
            "Third page requirement.",
        ]


def test_knowledge_pdf_import_saves_nonblank_pages(tmp_path):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    service = KnowledgeService.from_repository(repository)
    importer = KnowledgePDFImporter(
        parser=FakePDFParser()
    )

    chunks = importer.import_file(
        "source.pdf",
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        service=service,
    )

    assert chunks == [
        KnowledgeChunk(
            source_id="drawing-11240-24-as",
            source_title="Working documentation",
            page=1,
            text="First page requirement.",
        ),
        KnowledgeChunk(
            source_id="drawing-11240-24-as",
            source_title="Working documentation",
            page=3,
            text="Third page requirement.",
        ),
    ]
    assert repository.load() == chunks

class FakeOCRService:
    def __init__(self):
        self.calls = []

    def recognize_page(self, file_path, page_number):
        self.calls.append((file_path, page_number))

        return {
            "page": page_number,
            "text": "OCR second page requirement.",
            "ocr": True,
        }


def test_knowledge_pdf_import_uses_ocr_for_blank_pages(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    service = KnowledgeService.from_repository(repository)
    ocr_service = FakeOCRService()
    importer = KnowledgePDFImporter(
        parser=FakePDFParser(),
        ocr_service=ocr_service,
    )

    chunks = importer.import_file(
        "source.pdf",
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        service=service,
        ocr_empty_pages=True,
    )

    assert [chunk.page for chunk in chunks] == [1, 2, 3]
    assert chunks[1].text == "OCR second page requirement."
    assert ocr_service.calls == [
        ("source.pdf", 2),
    ]
    assert repository.load() == chunks
