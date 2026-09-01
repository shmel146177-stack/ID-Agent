from pypdf import PdfReader


class PDFParser:
    def extract_pages(self, file_path: str) -> list[str]:
        reader = PdfReader(file_path)

        return [
            page.extract_text() or ""
            for page in reader.pages
        ]

    def extract_text(self, file_path: str) -> str:
        return "".join(
            page_text + "\n"
            for page_text in self.extract_pages(file_path)
            if page_text
        )


pdf_parser = PDFParser()
