import pytest

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

    def recognize_page(
        self,
        file_path,
        page_number,
        dpi=300,
        psm=6,
    ):
        self.calls.append(
            (file_path, page_number, dpi, psm)
        )

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
        ocr_dpi=150,
        ocr_psm=4,
    )

    assert [chunk.page for chunk in chunks] == [1, 2, 3]
    assert chunks[1].text == "OCR second page requirement."
    assert chunks[0].text_origin == "native"
    assert chunks[0].requires_human_review is False
    assert chunks[1].text_origin == "ocr"
    assert chunks[1].requires_human_review is True
    assert ocr_service.calls == [
        ("source.pdf", 2, 150, 4),
    ]
    assert repository.load() == chunks

@pytest.mark.parametrize("ocr_dpi", [0, -1])
def test_knowledge_pdf_import_rejects_nonpositive_ocr_dpi(
    ocr_dpi,
):
    importer = KnowledgePDFImporter(
        parser=FakePDFParser(),
        ocr_service=FakeOCRService(),
    )

    with pytest.raises(
        ValueError,
        match="ocr_dpi must be positive",
    ):
        importer.import_file(
            "source.pdf",
            source_id="drawing-11240-24-as",
            source_title="Working documentation",
            service=KnowledgeService(),
            ocr_empty_pages=True,
            ocr_dpi=ocr_dpi,
        )


def test_knowledge_pdf_import_replaces_selected_page(
    tmp_path,
):
    repository = KnowledgeRepository(
        tmp_path / "knowledge" / "chunks.json"
    )
    original = KnowledgeChunk(
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        page=2,
        text="Old OCR page text.",
        text_origin="ocr",
        requires_human_review=True,
    )
    repository.save([original])
    service = KnowledgeService.from_repository(repository)
    ocr_service = FakeOCRService()
    importer = KnowledgePDFImporter(
        parser=FakePDFParser(),
        ocr_service=ocr_service,
    )

    imported = importer.import_file(
        "source.pdf",
        source_id="drawing-11240-24-as",
        source_title="Working documentation",
        service=service,
        ocr_empty_pages=True,
        ocr_dpi=300,
        page_numbers={2},
        replace_existing_pages=True,
    )

    assert [chunk.page for chunk in imported] == [2]
    assert len(service.chunks) == 1
    assert service.chunks[0].text == (
        "OCR second page requirement."
    )
    assert repository.load() == service.chunks
    assert ocr_service.calls == [
        ("source.pdf", 2, 300, 6),
    ]
