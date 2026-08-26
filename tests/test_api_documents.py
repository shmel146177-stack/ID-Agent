import asyncio
from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile
from fastapi.testclient import TestClient
from app.models.ai_analysis import AIAnalysisResult

import app.api.documents as documents_module
from main import app


client = TestClient(app)


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
    assert "ai_analysis" not in result

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


def test_upload_document_pdf_with_explicit_ai(monkeypatch, tmp_path):
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
            "status": "Document detected",
        },
    )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        lambda file_path: "PDF document text",
    )

    deterministic_analysis = {
        "document_type": "deterministic-drawing",
        "drawing_number": "TEST-001",
    }

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        lambda text: deterministic_analysis,
    )

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        lambda data: None,
    )

    class AIClientStub:
        class Settings:
            active = True

        def __init__(self):
            self.settings = self.Settings()

    class AIServiceStub:
        @classmethod
        def with_openai(cls, ai_client=None):
            assert isinstance(ai_client, AIClientStub)
            return cls()

        def analyze_text(self, filename, text):
            assert filename == "test.pdf"
            assert text == "PDF document text"

            return AIAnalysisResult(
                summary="AI analysis completed.",
                document_type_suggestion="ai-passport",
            )

    monkeypatch.setattr(
        documents_module,
        "AIClient",
        AIClientStub,
        raising=False,
    )

    monkeypatch.setattr(
        documents_module,
        "AIDocumentAnalysisService",
        AIServiceStub,
        raising=False,
    )

    upload = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"PDF DATA"),
    )

    result = asyncio.run(
        documents_module.upload_document(
            upload,
            use_ai=True,
        )
    )

    assert result["document_type"] == "deterministic-drawing"
    assert result["drawing_number"] == "TEST-001"

    assert result["ai_analysis"]["summary"] == "AI analysis completed."
    assert (
        result["ai_analysis"]["document_type_suggestion"]
        == "ai-passport"
    )
    assert result["ai_analysis"]["requires_human_review"] is True
    assert result["ai_analysis"]["engineering_confirmation"] is False


def test_upload_document_http_with_explicit_ai(monkeypatch, tmp_path):
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
            "status": "Document detected",
        },
    )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        lambda file_path: "PDF document text",
    )

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        lambda text: {
            "document_type": "deterministic-drawing",
            "drawing_number": "TEST-001",
        },
    )

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        lambda data: None,
    )

    class AIClientStub:
        class Settings:
            active = True

        def __init__(self):
            self.settings = self.Settings()

    class AIServiceStub:
        @classmethod
        def with_openai(cls, ai_client=None):
            return cls()

        def analyze_text(self, filename, text):
            return AIAnalysisResult(
                summary="AI analysis completed.",
                document_type_suggestion="ai-passport",
            )

    monkeypatch.setattr(
        documents_module,
        "AIClient",
        AIClientStub,
    )

    monkeypatch.setattr(
        documents_module,
        "AIDocumentAnalysisService",
        AIServiceStub,
    )

    response = client.post(
        "/upload?use_ai=true",
        files={
            "file": (
                "test.pdf",
                b"PDF DATA",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["document_type"] == "deterministic-drawing"
    assert result["drawing_number"] == "TEST-001"

    assert result["ai_analysis"]["summary"] == "AI analysis completed."
    assert (
        result["ai_analysis"]["document_type_suggestion"]
        == "ai-passport"
    )
    assert result["ai_analysis"]["requires_human_review"] is True
    assert result["ai_analysis"]["engineering_confirmation"] is False


def test_upload_document_http_ai_unconfigured_falls_back(
    monkeypatch,
    tmp_path,
):
    upload_dir = tmp_path / "uploads"

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ID_AGENT_AI_ENABLED", raising=False)

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
            "status": "Document detected",
        },
    )

    monkeypatch.setattr(
        documents_module.pdf_parser,
        "extract_text",
        lambda file_path: "PDF document text",
    )

    monkeypatch.setattr(
        documents_module.document_analyzer,
        "analyze_text",
        lambda text: {
            "document_type": "deterministic-drawing",
            "drawing_number": "TEST-001",
        },
    )

    monkeypatch.setattr(
        documents_module.project_service,
        "save_analysis",
        lambda data: None,
    )

    response = client.post(
        "/upload?use_ai=true",
        files={
            "file": (
                "test.pdf",
                b"PDF DATA",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["document_type"] == "deterministic-drawing"
    assert result["drawing_number"] == "TEST-001"

    ai_analysis = result["ai_analysis"]

    assert "OpenAI API" in ai_analysis["summary"]
    assert "OPENAI_API_KEY" in ai_analysis["warnings"][0]
    assert ai_analysis["requires_human_review"] is True
    assert ai_analysis["engineering_confirmation"] is False
