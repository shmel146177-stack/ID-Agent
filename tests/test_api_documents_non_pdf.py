from io import BytesIO

from starlette.datastructures import UploadFile

import app.api.documents as documents_module


def test_upload_document_non_pdf_skips_pdf_analysis(
    monkeypatch,
    tmp_path,
):

    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(
        documents_module,
        "UPLOAD_DIR",
        str(upload_dir),
    )

    monkeypatch.setattr(
        documents_module.document_service,
        "analyze",
        lambda file_path: {
            "filename": "test.docx",
            "extension": ".docx",
            "size_bytes": 9,
            "status": "Документ определён",
        },
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "PDF-анализ не должен вызываться для DOCX"
        )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        fail_if_called,
    )

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        fail_if_called,
    )

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        fail_if_called,
    )

    upload = UploadFile(
        filename="test.docx",
        file=BytesIO(b"DOCX DATA"),
    )

    import asyncio

    result = asyncio.run(
        documents_module.upload_document(upload)
    )

    saved_file = upload_dir / "test.docx"

    assert saved_file.exists()
    assert saved_file.read_bytes() == b"DOCX DATA"

    assert result["filename"] == "test.docx"
    assert result["extension"] == ".docx"


def test_upload_document_non_pdf_does_not_call_ai(
    monkeypatch,
    tmp_path,
):
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(
        documents_module,
        "UPLOAD_DIR",
        str(upload_dir),
    )

    monkeypatch.setattr(
        documents_module.document_service,
        "analyze",
        lambda file_path: {
            "filename": "test.docx",
            "extension": ".docx",
            "size_bytes": 9,
            "status": "Document detected",
        },
    )

    class ForbiddenAIClient:
        def __init__(self):
            raise AssertionError("AI must not be called for non-PDF")

    monkeypatch.setattr(
        documents_module,
        "AIClient",
        ForbiddenAIClient,
    )

    upload = UploadFile(
        filename="test.docx",
        file=BytesIO(b"DOCX DATA"),
    )

    import asyncio

    result = asyncio.run(
        documents_module.upload_document(
            upload,
            use_ai=True,
        )
    )

    assert result["filename"] == "test.docx"
    assert result["extension"] == ".docx"
    assert "ai_analysis" not in result
