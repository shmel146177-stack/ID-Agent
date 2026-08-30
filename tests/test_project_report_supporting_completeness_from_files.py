from app.generators.project_report_generator import ProjectReportGenerator


def test_report_enriches_supporting_sections_with_actual_file_counts(tmp_path, monkeypatch):
    generator = ProjectReportGenerator()

    executive_root = tmp_path / "executive_docs" / "Исполнительная_документация"
    section_04 = executive_root / "04_Исполнительные_схемы"
    section_04.mkdir(parents=True)

    (section_04 / "scheme_1.pdf").write_bytes(b"PDF")

    monkeypatch.setattr(
        generator,
        "_project_path",
        lambda project_name: tmp_path,
    )

    supporting_documents = {
        "sections": [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
                "required_count": 2,
                "documents": [],
            },
        ],
    }

    result = generator._with_supporting_completeness(
        "TEST_PROJECT",
        supporting_documents,
    )

    section = result["sections"][0]

    assert section["required_count"] == 2
    assert section["found_count"] == 1
    assert section["missing_count"] == 1
