from pathlib import Path

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
