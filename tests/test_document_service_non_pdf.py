import app.services.document_service as service_module
from app.services.document_service import DocumentService


def test_document_service_non_pdf_skips_pdf_parser(
    monkeypatch,
    tmp_path,
):

    service = DocumentService()

    file_path = tmp_path / "notes.txt"
    file_path.write_bytes(b"HELLO")

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "PDF parser не должен вызываться для TXT"
        )

    monkeypatch.setattr(
        service_module.pdf_parser,
        "extract_text",
        fail_if_called,
    )

    result = service.analyze(
        str(file_path)
    )

    assert result["filename"] == "notes.txt"
    assert result["extension"] == ".txt"
    assert result["size_bytes"] == 5
    assert "status" in result

    assert "pages_text_length" not in result
    assert "preview" not in result
