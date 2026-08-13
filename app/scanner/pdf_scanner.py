import fitz


class PDFScanner:

    def read(self, file_path):

        doc = fitz.open(file_path)

        text = ""

        for page in doc:
            text += page.get_text()

        return {
            "pages": len(doc),
            "text": text
        }