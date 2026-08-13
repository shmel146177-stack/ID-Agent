import app.scanner.pdf_scanner as scanner_module
from app.scanner.pdf_scanner import PDFScanner


def test_pdf_scanner_reads_pages_and_text(monkeypatch):

    class FakePage:

        def __init__(self, text):
            self.text = text

        def get_text(self):
            return self.text

    class FakeDocument:

        def __init__(self):
            self.pages = [
                FakePage("Первая страница\n"),
                FakePage("Вторая страница\n"),
                FakePage("Третья страница\n"),
            ]

        def __iter__(self):
            return iter(self.pages)

        def __len__(self):
            return len(self.pages)

    fake_document = FakeDocument()

    monkeypatch.setattr(
        scanner_module.fitz,
        "open",
        lambda file_path: fake_document,
    )

    scanner = PDFScanner()

    result = scanner.read(
        "test.pdf"
    )

    assert result["pages"] == 3
    assert result["text"] == (
        "Первая страница\n"
        "Вторая страница\n"
        "Третья страница\n"
    )
