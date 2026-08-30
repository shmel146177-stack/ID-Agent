import os

import pytest

from app.services.executive_document_router import ExecutiveDocumentRouter


def test_executive_document_router_routes_and_reports(monkeypatch, tmp_path):

    router = ExecutiveDocumentRouter()

    project_name = "TEST_PROJECT"

    source_folder = tmp_path / "source"
    executive_root = tmp_path / "executive"

    source_folder.mkdir(parents=True)

    certificate = source_folder / "certificate.pdf"
    protocol = source_folder / "protocol.pdf"

    certificate.write_bytes(b"CERTIFICATE")
    protocol.write_bytes(b"PROTOCOL")

    missing_file = source_folder / "missing.pdf"

    project_analysis = {
        "documents": [
            {
                "filename": certificate.name,
                "classification": "Сертификат",
                "path": str(certificate),
            },
            {
                "filename": protocol.name,
                "classification": "Протокол",
                "path": str(protocol),
            },
            {
                "filename": "drawing.pdf",
                "classification": "Чертеж",
                "path": str(source_folder / "drawing.pdf"),
            },
            {
                "filename": "without_path.pdf",
                "classification": "Сертификат",
            },
            {
                "filename": missing_file.name,
                "classification": "Сертификат",
                "path": str(missing_file),
            },
        ]
    }

    monkeypatch.setattr(
        router,
        "_load_project_analysis",
        lambda name: project_analysis,
    )

    monkeypatch.setattr(
        router,
        "_section_folders",
        lambda: {
            "quality_documents": "quality",
            "tests": "tests",
        },
    )

    monkeypatch.setattr(
        router,
        "_executive_root",
        lambda name: executive_root,
    )

    result = router.route(project_name)

    assert result["project"] == project_name

    assert result["routed_count"] == 2
    assert result["skipped_count"] == 1
    assert result["missing_source_count"] == 2

    routed_certificate = executive_root / "quality" / certificate.name
    routed_protocol = executive_root / "tests" / protocol.name

    assert routed_certificate.exists()
    assert routed_protocol.exists()

    assert routed_certificate.read_bytes() == b"CERTIFICATE"
    assert routed_protocol.read_bytes() == b"PROTOCOL"

    assert result["routed"][0]["section"] == "quality_documents"
    assert result["routed"][1]["section"] == "tests"

    assert result["skipped"][0]["reason"] == "no_route"

    reasons = {
        item["reason"]
        for item in result["missing_source"]
    }

    assert reasons == {
        "path_missing",
        "source_not_found",
    }


def test_router_keeps_identical_existing_document_unchanged(
    monkeypatch,
    tmp_path,
):
    router = ExecutiveDocumentRouter()
    source = tmp_path / "source" / "protocol.pdf"
    destination = tmp_path / "executive" / "tests" / source.name
    source.parent.mkdir()
    destination.parent.mkdir(parents=True)
    source.write_bytes(b"PROTOCOL")
    destination.write_bytes(b"PROTOCOL")
    os.utime(destination, (1_000_000_000, 1_000_000_000))
    original_mtime = destination.stat().st_mtime_ns

    monkeypatch.setattr(
        router,
        "_load_project_analysis",
        lambda name: {
            "documents": [
                {
                    "filename": source.name,
                    "classification": "Протокол",
                    "path": str(source),
                }
            ]
        },
    )
    monkeypatch.setattr(
        router,
        "_section_folders",
        lambda: {"tests": "tests"},
    )
    monkeypatch.setattr(
        router,
        "_executive_root",
        lambda name: tmp_path / "executive",
    )

    result = router.route("TEST_PROJECT")

    assert result["routed_count"] == 0
    assert result["already_routed_count"] == 1
    assert result["conflict_count"] == 0
    assert result["already_routed"][0]["reason"] == (
        "already_routed_same_content"
    )
    assert destination.read_bytes() == b"PROTOCOL"
    assert destination.stat().st_mtime_ns == original_mtime


def test_router_reports_conflict_without_overwriting_existing_document(
    monkeypatch,
    tmp_path,
):
    router = ExecutiveDocumentRouter()
    source = tmp_path / "source" / "certificate.pdf"
    destination = tmp_path / "executive" / "quality" / source.name
    source.parent.mkdir()
    destination.parent.mkdir(parents=True)
    source.write_bytes(b"NEW CERTIFICATE")
    destination.write_bytes(b"ORIGINAL CERTIFICATE")

    monkeypatch.setattr(
        router,
        "_load_project_analysis",
        lambda name: {
            "documents": [
                {
                    "filename": source.name,
                    "classification": "Сертификат",
                    "path": str(source),
                }
            ]
        },
    )
    monkeypatch.setattr(
        router,
        "_section_folders",
        lambda: {"quality_documents": "quality"},
    )
    monkeypatch.setattr(
        router,
        "_executive_root",
        lambda name: tmp_path / "executive",
    )

    result = router.route("TEST_PROJECT")

    assert result["routed_count"] == 0
    assert result["already_routed_count"] == 0
    assert result["conflict_count"] == 1
    assert result["conflicts"][0]["reason"] == (
        "destination_exists_different_content"
    )
    assert destination.read_bytes() == b"ORIGINAL CERTIFICATE"


def test_router_removes_new_partial_destination_after_copy_error(
    monkeypatch,
    tmp_path,
):
    router = ExecutiveDocumentRouter()
    source = tmp_path / "source" / "protocol.pdf"
    destination = tmp_path / "executive" / "tests" / source.name
    source.parent.mkdir()
    source.write_bytes(b"PROTOCOL")

    monkeypatch.setattr(
        router,
        "_load_project_analysis",
        lambda name: {
            "documents": [
                {
                    "filename": source.name,
                    "classification": "Протокол",
                    "path": str(source),
                }
            ]
        },
    )
    monkeypatch.setattr(
        router,
        "_section_folders",
        lambda: {"tests": "tests"},
    )
    monkeypatch.setattr(
        router,
        "_executive_root",
        lambda name: tmp_path / "executive",
    )

    def fail_copy(source_file, destination_file):
        destination_file.write(b"PARTIAL")
        raise OSError("copy failed")

    monkeypatch.setattr(
        "app.services.executive_document_router.shutil.copyfileobj",
        fail_copy,
    )

    with pytest.raises(OSError, match="copy failed"):
        router.route("TEST_PROJECT")

    assert not destination.exists()
