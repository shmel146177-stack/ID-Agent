import asyncio
from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile

import app.api.documents as documents_module


def test_upload_document_pdf_pipeline(monkeypatch, tmp_path):

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
            "filename": "test.pdf",
            "extension": ".pdf",
            "size_bytes": 8,
            "status": "Документ определён",
        },
    )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        lambda file_path: "Тестовый текст PDF",
    )

    analysis = {
        "document_type": "Чертеж",
        "drawing_number": "TEST-001",
    }

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        lambda text: analysis,
    )

    saved_analysis = {}

    def fake_save_analysis(data):
        saved_analysis.update(data)
        return {
            "status": "Анализ сохранён",
            "document": data,
        }

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        fake_save_analysis,
    )

    upload = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"PDF DATA"),
    )

    result = asyncio.run(
        documents_module.upload_document(upload)
    )

    saved_file = upload_dir / "test.pdf"

    assert saved_file.exists()
    assert saved_file.read_bytes() == b"PDF DATA"

    assert result["filename"] == "test.pdf"
    assert result["extension"] == ".pdf"
    assert result["document_type"] == "Чертеж"
    assert result["drawing_number"] == "TEST-001"

    assert saved_analysis == analysis


def test_upload_document_sanitizes_windows_filename_path(
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
            "filename": "safe.docx",
            "extension": ".docx",
            "size_bytes": 4,
            "status": "Документ определён",
        },
    )

    upload = UploadFile(
        filename=r"..\..\safe.docx",
        file=BytesIO(b"SAFE"),
    )

    result = asyncio.run(
        documents_module.upload_document(upload)
    )

    saved_file = upload_dir / "safe.docx"

    assert saved_file.read_bytes() == b"SAFE"
    assert result["filename"] == "safe.docx"
    assert not (tmp_path / "safe.docx").exists()
