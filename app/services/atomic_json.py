import json
import os
from uuid import uuid4


def write_json_atomically(path: str, data: dict) -> None:
    """Durably replace one JSON file without exposing partial content."""
    directory = os.path.dirname(path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    temporary_path = f"{path}.{uuid4().hex}.tmp"

    try:
        with open(
            temporary_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4,
            )
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
