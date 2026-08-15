from pathlib import Path

from app.services.executive_document_router import ExecutiveDocumentRouter


def test_router_sends_executive_scheme_to_section_04(tmp_path, monkeypatch):
    router = ExecutiveDocumentRouter()

    source = tmp_path / "executive_scheme.pdf"
    source.write_bytes(b"PDF")

    executive_root = tmp_path / "executive_docs"

    monkeypatch.setattr(
        router,
        "_executive_root",
        lambda project_name: executive_root,
    )

    monkeypatch.setattr(
        router,
        "_load_project_analysis",
        lambda project_name: {
            "documents": [
                {
                    "filename": source.name,
                    "classification": "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
                    "path": str(source),
                },
            ],
        },
    )

    result = router.route("TEST_PROJECT")

    assert result["routed_count"] == 1
    assert result["skipped_count"] == 0
    assert result["routed"][0]["section"] == "executive_schemes"

    destination = Path(result["routed"][0]["destination"])
    assert destination.is_file()
    assert destination.name == source.name
