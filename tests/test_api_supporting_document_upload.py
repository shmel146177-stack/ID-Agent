from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

import app.api.project_processor as api_module
from app.services.supporting_document_upload import (
    SupportingDocumentTooLargeError,
)


def test_supporting_upload_api_delegates_and_closes_file(monkeypatch):
    received = {}

    def fake_upload(project_name, section_code, filename, source):
        received.update(
            {
                "project_name": project_name,
                "section_code": section_code,
                "filename": filename,
                "content": source.read(),
            }
        )
        return {
            "status": "Файл загружен и проект повторно проанализирован",
            "upload_verification": {
                "status": "Подтверждён",
            },
        }

    monkeypatch.setattr(
        api_module.supporting_document_upload,
        "upload",
        fake_upload,
    )

    upload = UploadFile(
        filename=r"C:\incoming\grounding_protocol.pdf",
        file=BytesIO(b"PROTOCOL"),
    )

    result = api_module.upload_supporting_document(
        "Реальный_объект",
        "tests",
        upload,
    )

    assert result["upload_verification"]["status"] == "Подтверждён"
    assert received == {
        "project_name": "Реальный_объект",
        "section_code": "tests",
        "filename": r"C:\incoming\grounding_protocol.pdf",
        "content": b"PROTOCOL",
    }
    assert upload.file.closed is True


@pytest.mark.parametrize(
    ("raised_error", "expected_status"),
    [
        (SupportingDocumentTooLargeError("Файл слишком большой"), 413),
        (ValueError("Неверный раздел"), 400),
        (FileNotFoundError("Проект не найден"), 404),
        (FileExistsError("Файл уже существует"), 409),
        (RuntimeError("Ошибка анализа"), 500),
    ],
)
def test_supporting_upload_api_maps_errors_and_closes_file(
    monkeypatch,
    raised_error,
    expected_status,
):
    def raise_error(*args, **kwargs):
        raise raised_error

    monkeypatch.setattr(
        api_module.supporting_document_upload,
        "upload",
        raise_error,
    )

    upload = UploadFile(
        filename="document.pdf",
        file=BytesIO(b"DOCUMENT"),
    )

    with pytest.raises(HTTPException) as error:
        api_module.upload_supporting_document(
            "TEST_PROJECT",
            "tests",
            upload,
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == str(raised_error)
    assert upload.file.closed is True
