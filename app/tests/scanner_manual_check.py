from app.scanner.scanner import DocumentScanner

scanner = DocumentScanner()

doc = scanner.scan(
    "uploads/АЭП40-016-54К-22У_17.08.23 (1).pdf"
)

print(doc.filename)
print(doc.pages)
print(len(doc.text))
