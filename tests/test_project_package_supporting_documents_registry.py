from app.services.project_package import ProjectPackage


def test_project_package_copies_supporting_documents_registry(monkeypatch, tmp_path):
    package = ProjectPackage()

    project_name = "TEST_PROJECT"
    project_path = tmp_path / project_name
    analysis_path = project_path / "analysis"
    destination_path = tmp_path / "package"

    analysis_path.mkdir(parents=True)

    source = analysis_path / "supporting_documents_registry.json"
    source.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        package,
        "_project_path",
        lambda name: project_path,
    )

    copied = package._copy_analysis_files(
        project_name,
        destination_path,
    )

    expected = destination_path / "supporting_documents_registry.json"

    assert expected.exists()
    assert str(expected) in copied
