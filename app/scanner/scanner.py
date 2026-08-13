from pathlib import Path

from app.models.document_model import DocumentModel
from app.scanner.pdf_scanner import PDFScanner


class DocumentScanner:
    def __init__(self):
        self.pdf = PDFScanner()

    def scan(self, file_path: str) -> DocumentModel:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(file_path)

        model = DocumentModel(
            filename=path.name,
            extension=path.suffix.lower()
        )

        if model.extension == ".pdf":
            result = self.pdf.read(file_path)
            model.pages = result["pages"]
            model.text = result["text"]

        return model