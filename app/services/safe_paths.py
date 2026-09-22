"""Portable path validation for project storage and uploaded filenames."""
from pathlib import Path

WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT")
    for number in "123456789¹²³"
}


def validate_name(name: str) -> str:
    if (
        not name or name != name.strip() or name in {".", ".."}
        or name.endswith(".")
        or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in name)
        or name.split(".")[0].rstrip(" ").upper() in WINDOWS_RESERVED_NAMES
    ):
        raise ValueError("Некорректное имя файла или проекта")
    return name


def safe_project_path(project_name: str, projects_root="projects") -> Path:
    try:
        validate_name(project_name)
    except ValueError as error:
        raise ValueError("Некорректное имя проекта") from error
    root = Path(projects_root).resolve()
    path = Path(projects_root) / project_name
    if path.resolve().parent != root:
        raise ValueError("Путь проекта выходит за корень projects")
    return path


def safe_child_path(root, *parts: str) -> Path:
    path = Path(root).joinpath(*parts)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("Путь выходит за разрешенный каталог")
    return path
