import app.parsers.pdf_parser as parser_module
from app.parsers.pdf_parser import PDFParser


def test_pdf_parser_extracts_text_from_pages(monkeypatch):

    class FakePage:

        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class FakeReader:

        def __init__(self, file_path):
            self.pages = [
                FakePage("Первая страница"),
                FakePage(None),
                FakePage("Третья страница"),
            ]

    monkeypatch.setattr(
        parser_module,
        "PdfReader",
        FakeReader,
    )

    parser = PDFParser()

    result = parser.extract_text(
        "test.pdf"
    )

    assert result == (
        "Первая страница\n"
        "Третья страница\n"
    )
