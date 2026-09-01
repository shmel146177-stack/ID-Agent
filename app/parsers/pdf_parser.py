import fitz
from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFParser:
    def extract_pages(self, file_path: str) -> list[str]:
        try:
            reader = PdfReader(file_path)

            return [
                page.extract_text() or ""
                for page in reader.pages
            ]
        except PdfReadError:
            with fitz.open(file_path) as document:
                return [
                    page.get_text() or ""
                    for page in document
                ]

    def extract_text(self, file_path: str) -> str:
        return "".join(
            page_text + "\n"
            for page_text in self.extract_pages(file_path)
            if page_text
        )


pdf_parser = PDFParser()
