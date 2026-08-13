import os

from app.parsers.pdf_parser import pdf_parser


class DocumentService:

    def analyze(self, file_path: str):
        filename = os.path.basename(file_path)
        extension = os.path.splitext(filename)[1]
        size = os.path.getsize(file_path)

        result = {
            "filename": filename,
            "extension": extension,
            "size_bytes": size,
            "status": "Документ определён"
        }

        if extension.lower() == ".pdf":
            text = pdf_parser.extract_text(file_path)

            result["pages_text_length"] = len(text)
            result["preview"] = text[:500]

        return result


document_service = DocumentService()