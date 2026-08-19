from io import BytesIO

import pytest

from app.services.supporting_document_upload import (
    SupportingDocumentUpload,
)


class ProcessorStub:
    def __init__(self, result=None, error=None):
        self.result = result or {}
        self.error = error
        self.calls = []

    def process(self, project_name: str) -> dict:
        self.calls.append(project_name)

        if self.error is not None:
            raise self.error

        return self.result


class BrokenStream:
    def __init__(self):
        self.read_count = 0

    def read(self, size=-1):
        self.read_count += 1

        if self.read_count == 1:
            return b"PARTIAL"

        raise OSError("Ошибка чтения")


def create_service(tmp_path, processor=None):
    service = SupportingDocumentUpload(processor=processor)
    service.projects_root = tmp_path
    (tmp_path / "TEST_PROJECT").mkdir()
    return service


def test_upload_saves_file_and_reanalyzes_target_section(tmp_path):
    processor = ProcessorStub(
        {
            "supporting_documents": {
                "sections": [
                    {
                        "code": "tests",
                        "found_count": 1,
                        "missing_count": 1,
                    }
                ],
                "requirements": [
                    {
                        "code": "grounding_resistance_protocol",
                        "section_code": "tests",
                    }
                ],
                "matching": {
                    "matched": [
                        {
                            "requirement_code": (
                                "grounding_resistance_protocol"
                            ),
                            "filename": "grounding_protocol.pdf",
                            "classification": "Протокол",
                        }
                    ]
                },
            }
        }
    )
    service = create_service(tmp_path, processor)

    result = service.upload(
        "TEST_PROJECT",
        "tests",
        r"C:\incoming\grounding_protocol.pdf",
        BytesIO(b"%PDF-1.7 protocol"),
    )

    saved_file = (
        tmp_path
        / "TEST_PROJECT"
        / "input"
        / "grounding_protocol.pdf"
    )

    assert saved_file.read_bytes() == b"%PDF-1.7 protocol"
    assert processor.calls == ["TEST_PROJECT"]
    assert result["automatic_processing"]["status"] == "Готово"
    assert result["target_section"]["number"] == "05"
    assert result["section_analysis"]["found_count"] == 1
    assert result["upload_verification"]["status"] == "Подтверждён"
    assert result["upload_verification"]["matched_requirements"][0][
        "requirement_code"
    ] == "grounding_resistance_protocol"
    assert result["upload_verification"]["routing_conflicts"] == []


@pytest.mark.parametrize(
    "section_code",
    ["executive_schemes", "tests", "quality_documents"],
)
def test_upload_accepts_only_managed_sections(tmp_path, section_code):
    service = create_service(tmp_path, ProcessorStub())

    result = service.upload(
        "TEST_PROJECT",
        section_code,
        f"{section_code}.pdf",
        BytesIO(b"document"),
    )

    assert result["target_section"]["code"] == section_code


def test_upload_rejects_unknown_section_before_writing(tmp_path):
    service = create_service(tmp_path, ProcessorStub())

    with pytest.raises(ValueError, match="Раздел должен быть"):
        service.upload(
            "TEST_PROJECT",
            "journals",
            "journal.pdf",
            BytesIO(b"document"),
        )

    assert not (tmp_path / "TEST_PROJECT" / "input").exists()


@pytest.mark.parametrize(
    "project_name",
    [
        "",
        ".",
        "..",
        "../OUTSIDE",
        r"..\OUTSIDE",
        "/tmp/OUTSIDE",
        r"C:\Projects\OUTSIDE",
    ],
)
def test_upload_rejects_project_path_traversal(
    tmp_path,
    project_name,
):
    service = SupportingDocumentUpload(processor=ProcessorStub())
    service.projects_root = tmp_path

    with pytest.raises(ValueError, match="имя проекта"):
        service.upload(
            project_name,
            "tests",
            "protocol.pdf",
            BytesIO(b"document"),
        )


def test_upload_rejects_project_symlink_outside_root(tmp_path):
    projects_root = tmp_path / "projects"
    projects_root.mkdir()
    outside_project = tmp_path / "outside"
    outside_project.mkdir()
    try:
        (projects_root / "LINK").symlink_to(
            outside_project,
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("Создание симлинков недоступно в этой среде")

    service = SupportingDocumentUpload(processor=ProcessorStub())
    service.projects_root = projects_root

    with pytest.raises(ValueError, match="выходит за корень"):
        service.upload(
            "LINK",
            "tests",
            "protocol.pdf",
            BytesIO(b"document"),
        )

    assert not (outside_project / "input").exists()


def test_upload_rejects_duplicate_without_overwriting(tmp_path):
    service = create_service(tmp_path, ProcessorStub())
    input_path = tmp_path / "TEST_PROJECT" / "input"
    input_path.mkdir()
    saved_file = input_path / "protocol.pdf"
    saved_file.write_bytes(b"original")

    with pytest.raises(FileExistsError, match="уже существует"):
        service.upload(
            "TEST_PROJECT",
            "tests",
            "protocol.pdf",
            BytesIO(b"replacement"),
        )

    assert saved_file.read_bytes() == b"original"


def test_upload_removes_partial_file_after_copy_error(tmp_path):
    service = create_service(tmp_path, ProcessorStub())

    with pytest.raises(OSError, match="Ошибка чтения"):
        service.upload(
            "TEST_PROJECT",
            "tests",
            "protocol.pdf",
            BrokenStream(),
        )

    assert not (
        tmp_path
        / "TEST_PROJECT"
        / "input"
        / "protocol.pdf"
    ).exists()


def test_upload_keeps_file_when_reanalysis_fails(tmp_path):
    service = create_service(
        tmp_path,
        ProcessorStub(error=RuntimeError("OCR unavailable")),
    )

    result = service.upload(
        "TEST_PROJECT",
        "quality_documents",
        "certificate.pdf",
        BytesIO(b"certificate"),
    )

    saved_file = (
        tmp_path
        / "TEST_PROJECT"
        / "input"
        / "certificate.pdf"
    )

    assert saved_file.exists()
    assert result["automatic_processing"] == {
        "status": "Ошибка анализа",
        "error": "OCR unavailable",
        "result": None,
    }
    assert result["upload_verification"]["status"] == "Не выполнена"


def test_upload_reports_match_in_another_section(tmp_path):
    processor = ProcessorStub(
        {
            "supporting_documents": {
                "sections": [],
                "requirements": [
                    {
                        "code": "grounding_quality_documents",
                        "section_code": "quality_documents",
                    }
                ],
                "matching": {
                    "matched": [
                        {
                            "requirement_code": (
                                "grounding_quality_documents"
                            ),
                            "filename": "document.pdf",
                            "classification": "Сертификат",
                        }
                    ]
                },
            }
        }
    )
    service = create_service(tmp_path, processor)

    result = service.upload(
        "TEST_PROJECT",
        "tests",
        "document.pdf",
        BytesIO(b"certificate"),
    )

    verification = result["upload_verification"]

    assert verification["status"] == "Раздел не совпадает"
    assert verification["matched_requirements"] == []
    assert verification["other_section_matches"][0][
        "section_code"
    ] == "quality_documents"


def test_upload_reports_routing_conflict_before_confirmed_match(tmp_path):
    processor = ProcessorStub(
        {
            "document_routing": {
                "conflicts": [
                    {
                        "filename": "grounding_protocol.pdf",
                        "classification": "Протокол",
                        "section": "tests",
                        "destination": (
                            "executive_docs/05/grounding_protocol.pdf"
                        ),
                        "reason": (
                            "destination_exists_different_content"
                        ),
                    }
                ]
            },
            "supporting_documents": {
                "sections": [],
                "requirements": [
                    {
                        "code": "grounding_resistance_protocol",
                        "section_code": "tests",
                    }
                ],
                "matching": {
                    "matched": [
                        {
                            "requirement_code": (
                                "grounding_resistance_protocol"
                            ),
                            "filename": "grounding_protocol.pdf",
                            "classification": "Протокол",
                        }
                    ]
                },
            },
        }
    )
    service = create_service(tmp_path, processor)

    result = service.upload(
        "TEST_PROJECT",
        "tests",
        "grounding_protocol.pdf",
        BytesIO(b"NEW PROTOCOL"),
    )

    verification = result["upload_verification"]

    assert result["status"] == (
        "Файл загружен, но обнаружен конфликт маршрутизации"
    )
    assert verification["status"] == "Конфликт маршрутизации"
    assert verification["matched_requirements"][0][
        "requirement_code"
    ] == "grounding_resistance_protocol"
    assert verification["routing_conflicts"][0]["section"] == "tests"
    assert verification["routing_conflicts"][0]["reason"] == (
        "destination_exists_different_content"
    )


def test_upload_does_not_confirm_preexisting_matched_file(tmp_path):
    processor = ProcessorStub(
        {
            "supporting_documents": {
                "sections": [],
                "requirements": [
                    {
                        "code": "grounding_resistance_protocol",
                        "section_code": "tests",
                    }
                ],
                "matching": {
                    "matched": [
                        {
                            "requirement_code": (
                                "grounding_resistance_protocol"
                            ),
                            "filename": "old_protocol.pdf",
                            "classification": "Протокол",
                        }
                    ]
                },
            }
        }
    )
    service = create_service(tmp_path, processor)

    result = service.upload(
        "TEST_PROJECT",
        "tests",
        "new_protocol.pdf",
        BytesIO(b"new protocol"),
    )

    assert result["upload_verification"] == {
        "status": "Не подтверждён",
        "target_section_code": "tests",
        "filename": "new_protocol.pdf",
        "matched_requirements": [],
        "other_section_matches": [],
        "routing_conflicts": [],
    }


def test_upload_rejects_empty_file_and_removes_it(tmp_path):
    service = create_service(tmp_path, ProcessorStub())

    with pytest.raises(ValueError, match="Пустой файл"):
        service.upload(
            "TEST_PROJECT",
            "executive_schemes",
            "scheme.pdf",
            BytesIO(b""),
        )

    assert not (
        tmp_path
        / "TEST_PROJECT"
        / "input"
        / "scheme.pdf"
    ).exists()
