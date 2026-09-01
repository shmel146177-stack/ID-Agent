from pypdf.errors import PdfReadError

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

def test_pdf_parser_extracts_pages_separately(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class FakeReader:
        def __init__(self, file_path):
            self.pages = [
                FakePage("First page"),
                FakePage(None),
                FakePage("Third page"),
            ]

    monkeypatch.setattr(
        parser_module,
        "PdfReader",
        FakeReader,
    )

    parser = PDFParser()

    assert parser.extract_pages("test.pdf") == [
        "First page",
        "",
        "Third page",
    ]

def test_pdf_parser_falls_back_to_pymupdf(monkeypatch):
    class FailingPage:
        def extract_text(self):
            raise PdfReadError("Invalid PDF content")

    class FakeReader:
        def __init__(self, file_path):
            self.pages = [FailingPage()]

    class FakeFitzPage:
        def __init__(self, text):
            self.text = text

        def get_text(self):
            return self.text

    class FakeFitzDocument:
        def __init__(self):
            self.pages = [
                FakeFitzPage("First fallback page"),
                FakeFitzPage("Second fallback page"),
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def __iter__(self):
            return iter(self.pages)

    class FakeFitz:
        @staticmethod
        def open(file_path):
            assert file_path == "broken.pdf"
            return FakeFitzDocument()

    monkeypatch.setattr(
        parser_module,
        "PdfReader",
        FakeReader,
    )
    monkeypatch.setattr(
        parser_module,
        "fitz",
        FakeFitz,
        raising=False,
    )

    parser = PDFParser()

    assert parser.extract_pages("broken.pdf") == [
        "First fallback page",
        "Second fallback page",
    ]
