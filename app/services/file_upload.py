"""Shared exclusive, bounded upload persistence."""
from pathlib import Path

from fastapi import HTTPException

from app.services.safe_paths import safe_child_path, validate_name

MAX_FILE_SIZE_BYTES = 512 * 1024 * 1024
COPY_CHUNK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg",
    ".png", ".tif", ".tiff",
}


def save_upload(file, directory, *, max_size=MAX_FILE_SIZE_BYTES,
                chunk_size=COPY_CHUNK_SIZE):
    """Return (path, size); never overwrite or remove a pre-existing file."""
    try:
        filename = (file.filename or "").replace("\\", "/").split("/")[-1]
        try:
            validate_name(filename)
            path = safe_child_path(directory, filename)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"Неподдерживаемый формат файла: {path.suffix or 'без расширения'}")
        Path(directory).mkdir(parents=True, exist_ok=True)
        try:
            destination = path.open("xb")
        except FileExistsError as error:
            raise HTTPException(409, f"Файл уже существует: {filename}") from error
        try:
            size = 0
            with destination:
                while chunk := file.file.read(chunk_size):
                    size += len(chunk)
                    if size > max_size:
                        raise HTTPException(413, "Файл превышает допустимый размер")
                    destination.write(chunk)
                if not size:
                    raise HTTPException(400, "Пустой файл не может быть загружен")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return str(path), size
    except OSError as error:
        raise HTTPException(500, "Ошибка сохранения файла") from error
    finally:
        file.file.close()
