from pathlib import Path

import pytest

import app.services.storage_inventory as inventory_module
from app.services.storage_inventory import inventory_storage


def test_inventory_reports_nested_sizes_without_touching_files(tmp_path: Path):
    source = tmp_path / "projects" / "object" / "input"
    source.mkdir(parents=True)
    source_file = source / "drawing.pdf"
    source_file.write_bytes(b"source")
    temporary = tmp_path / "tmp" / "cache"
    temporary.mkdir(parents=True)
    temporary_file = temporary / "scratch.bin"
    temporary_file.write_bytes(b"working")

    result = inventory_storage(tmp_path, depth=2)
    rows = {row["path"]: row for row in result["directories"]}

    assert result["complete"] is True
    assert result["total"]["bytes"] == 13
    assert result["total"]["files"] == 2
    assert rows[str(Path("projects"))]["bytes"] == 6
    assert rows[str(Path("projects"))]["category"] == "project data"
    assert rows[str(Path("tmp"))]["bytes"] == 7
    assert rows[str(Path("tmp"))]["category"] == "inspect manually"
    assert source_file.read_bytes() == b"source"
    assert temporary_file.read_bytes() == b"working"


def test_inventory_labels_engineering_projects_as_protected(tmp_path: Path):
    object_folder = tmp_path / "Работа" / "01_ИД" / "Объект"
    object_folder.mkdir(parents=True)
    (object_folder / "акт.pdf").write_bytes(b"issued")

    result = inventory_storage(tmp_path, depth=3)
    row = next(
        row
        for row in result["directories"]
        if row["path"] == str(Path("Работа") / "01_ИД" / "Объект")
    )

    assert row["category"] == "engineering projects"


def test_inventory_skips_symlink_outside_root(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (external / "private.pdf").write_bytes(b"outside")
    link = root / "linked"
    try:
        link.symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlinks are unavailable")

    result = inventory_storage(root)

    assert result["total"]["bytes"] == 0
    assert result["complete"] is False
    assert result["skipped_links"] == ["linked"]


def test_inventory_rejects_non_directory_root(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="directory"):
        inventory_storage(file_path)


def test_inventory_reports_unreadable_directory(monkeypatch, tmp_path: Path):
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    original_scandir = inventory_module.os.scandir

    def scandir(path):
        if Path(path) == restricted:
            raise PermissionError("access denied")
        return original_scandir(path)

    monkeypatch.setattr(inventory_module.os, "scandir", scandir)

    result = inventory_storage(tmp_path)

    assert result["complete"] is False
    assert len(result["errors"]) == 1
    assert result["errors"][0]["path"] == "restricted"
