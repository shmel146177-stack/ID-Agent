"""Read-only, metadata-based inventory of a local workspace."""

import argparse
import json
import os
import stat
import sys
from pathlib import Path

PROTECTED_PARTS = {
    ".git": "Git history",
    ".venv": "active environment",
    "projects": "project data",
    "uploads": "uploaded sources",
    "templates": "reference templates",
    "01_ИД": "engineering projects",
    "01_Исходники": "source documents",
    "03_Версии": "issued versions",
}
REVIEW_PARTS = {"tmp", ".pytest_cache", ".ruff_cache", "checkpoints"}
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _category(parts: tuple[str, ...]) -> str:
    for part in parts:
        if part in PROTECTED_PARTS:
            return PROTECTED_PARTS[part]
    if any(part in REVIEW_PARTS or part.startswith(".pytest-") for part in parts):
        return "inspect manually"
    if parts and ("-audit-" in parts[0].lower() or "-validation-" in parts[0].lower()):
        return "inspect manually"
    if "output" in parts:
        return "generated output; inspect manually"
    return "mixed or unknown"


def inventory_storage(root: Path, depth: int = 2) -> dict:
    """Count apparent bytes without reading contents or following reparse points."""
    if depth < 1:
        raise ValueError("depth must be positive")

    root = Path(root).expanduser()
    root_stat = root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or (
        getattr(root_stat, "st_file_attributes", 0) & REPARSE_POINT
    ):
        raise ValueError("inventory root must not be a reparse point")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("inventory root must be a directory")
    root = root.resolve(strict=True)

    totals = {(): {"bytes": 0, "files": 0, "directories": 0, "skipped_links": 0}}
    errors = []
    skipped_links = []
    stack = [(root, ())]

    def add_to_ancestors(parts: tuple[str, ...], field: str, amount: int = 1) -> None:
        last_depth = min(len(parts) - 1, depth)
        for level in range(last_depth + 1):
            totals[parts[:level]][field] += amount

    while stack:
        directory, directory_parts = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    parts = (*directory_parts, entry.name)
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(metadata.st_mode) or (
                            getattr(metadata, "st_file_attributes", 0) & REPARSE_POINT
                        ):
                            skipped_links.append(str(Path(*parts)))
                            add_to_ancestors(parts, "skipped_links")
                        elif stat.S_ISDIR(metadata.st_mode):
                            add_to_ancestors(parts, "directories")
                            if len(parts) <= depth:
                                totals[parts] = {
                                    "bytes": 0,
                                    "files": 0,
                                    "directories": 0,
                                    "skipped_links": 0,
                                }
                            stack.append((Path(entry.path), parts))
                        elif stat.S_ISREG(metadata.st_mode):
                            add_to_ancestors(parts, "bytes", metadata.st_size)
                            add_to_ancestors(parts, "files")
                        else:
                            skipped_links.append(str(Path(*parts)))
                            add_to_ancestors(parts, "skipped_links")
                    except OSError as error:
                        errors.append({"path": str(Path(*parts)), "error": str(error)})
        except OSError as error:
            errors.append({"path": str(Path(*directory_parts)), "error": str(error)})

    rows = [
        {
            "path": str(Path(*parts)) if parts else ".",
            "category": _category(parts),
            **counts,
        }
        for parts, counts in totals.items()
    ]
    rows.sort(key=lambda row: (-row["bytes"], row["path"]))
    return {
        "root": str(root),
        "complete": not errors and not skipped_links,
        "total": next(row for row in rows if row["path"] == "."),
        "directories": [row for row in rows if row["path"] != "."],
        "skipped_links": skipped_links,
        "errors": errors,
        "note": "Apparent sizes can double-count hard links and do not predict reclaimable disk space. No deletion is performed.",
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.depth < 1 or args.top < 1:
        parser.error("--depth and --top must be positive")
    try:
        result = inventory_storage(args.root, args.depth)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"Root: {result['root']}")
    print(
        f"Total: {result['total']['bytes']:,} bytes in {result['total']['files']:,} files"
    )
    print("Complete:", "yes" if result["complete"] else "no")
    print("MiB       Files     Category                         Relative path")
    for row in result["directories"][: args.top]:
        print(
            f"{row['bytes'] / 1048576:9.1f} {row['files']:9,} "
            f"{row['category']:<32} {row['path']}"
        )
    if result["skipped_links"]:
        print(f"Skipped links/reparse points: {len(result['skipped_links'])}")
        for path in result["skipped_links"][:10]:
            print(f"  {path}")
    if result["errors"]:
        print(f"Read errors: {len(result['errors'])}")
        for error in result["errors"][:10]:
            print(f"  {error['path']}: {error['error']}")
    print(result["note"])


if __name__ == "__main__":
    main()
