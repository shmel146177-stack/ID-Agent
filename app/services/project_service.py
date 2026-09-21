import json
import os
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
from uuid import uuid4

from app.services.atomic_json import write_json_atomically
from app.services.interprocess_lock import exclusive_file_lock


class ProjectStateConflictError(Exception):
    pass


def _serialized_review_state(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with exclusive_file_lock(self.ai_review_lock_path):
            return method(self, *args, **kwargs)

    return wrapper


class ProjectService:

    def __init__(self):
        self.file_path = "projects/data/current_analysis.json"
        self.ai_file_path = "projects/data/current_ai_analysis.json"
        self.ai_review_file_path = "projects/data/current_ai_review.json"
        self.ai_review_history_dir = "projects/data/ai_review_history"
        self.ai_comparison_file_path = (
            "projects/data/current_ai_comparison.json"
        )

    @property
    def ai_review_lock_path(self) -> str:
        return f"{self.ai_review_file_path}.lock"

    @_serialized_review_state
    def save_analysis(self, data: dict):

        self._archive_current_ai_review()
        write_json_atomically(self.file_path, data)

        if os.path.exists(self.ai_file_path):
            os.remove(self.ai_file_path)

        if os.path.exists(self.ai_review_file_path):
            os.remove(self.ai_review_file_path)

        if os.path.exists(self.ai_comparison_file_path):
            os.remove(self.ai_comparison_file_path)

        return {
            "status": "Анализ сохранён",
            "document": data
        }

    @_serialized_review_state
    def save_ai_analysis(
        self,
        data: dict,
        source_filename: str | None = None,
        knowledge_source_ids: list[str] | None = None,
    ):
        self._archive_current_ai_review()

        data_to_save = dict(data)
        data_to_save["analysis_id"] = str(uuid4())

        if source_filename is not None:
            data_to_save["source_filename"] = source_filename

        if knowledge_source_ids is not None:
            data_to_save["knowledge_source_ids"] = list(
                knowledge_source_ids
            )

        write_json_atomically(self.ai_file_path, data_to_save)

        if os.path.exists(self.ai_review_file_path):
            os.remove(self.ai_review_file_path)

        if os.path.exists(self.ai_comparison_file_path):
            os.remove(self.ai_comparison_file_path)

        return {
            "status": "AI-анализ сохранен",
            "document": data_to_save,
        }

    @_serialized_review_state
    def save_ai_comparison(
        self,
        data: dict,
        analysis_id: str,
        source_filename: str,
        knowledge_source_ids: list[str] | None = None,
    ):
        current_analysis = self.get_ai_analysis()

        if current_analysis is None:
            raise ProjectStateConflictError(
                "AI comparison has no current AI analysis"
            )

        if current_analysis.get("analysis_id") != analysis_id:
            raise ProjectStateConflictError(
                "AI comparison analysis id mismatch"
            )

        if current_analysis.get("source_filename") != source_filename:
            raise ProjectStateConflictError(
                "AI comparison source filename mismatch"
            )

        if current_analysis.get("knowledge_source_ids", []) != (
            knowledge_source_ids or []
        ):
            raise ProjectStateConflictError(
                "AI comparison knowledge sources mismatch"
            )

        data_to_save = dict(data)
        data_to_save["analysis_id"] = analysis_id
        data_to_save["source_filename"] = source_filename

        if knowledge_source_ids is not None:
            data_to_save["knowledge_source_ids"] = list(
                knowledge_source_ids
            )

        write_json_atomically(
            self.ai_comparison_file_path,
            data_to_save,
        )

        return {
            "status": "AI comparison saved",
            "document": data_to_save,
        }

    def get_ai_comparison(self):

        if not os.path.exists(
            self.ai_comparison_file_path
        ):
            return None

        with open(
            self.ai_comparison_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def save_ai_review(self, data: dict):
        write_json_atomically(self.ai_review_file_path, data)

        return {
            "status": "AI-review saved",
            "document": data,
        }

    def get_ai_review(self):

        if not os.path.exists(self.ai_review_file_path):
            return None

        with open(
            self.ai_review_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _ai_review_history_path(self, analysis_id: str) -> str:
        digest = sha256(analysis_id.encode("utf-8")).hexdigest()
        return os.path.join(
            self.ai_review_history_dir,
            f"{digest}.json",
        )

    def _archive_current_ai_review(self):
        review = self.get_ai_review()
        analysis = self.get_ai_analysis()

        if review is None or analysis is None:
            return None

        analysis_id = review.get("analysis_id")

        if (
            not analysis_id
            or analysis.get("analysis_id") != analysis_id
        ):
            return None

        archive_path = self._ai_review_history_path(analysis_id)

        archived_review = dict(review)
        archived_review["archived_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        write_json_atomically(archive_path, archived_review)

        return archive_path

    def get_ai_review_history(self, analysis_id: str):
        archive_path = self._ai_review_history_path(analysis_id)

        if not os.path.exists(archive_path):
            return None

        with open(
            archive_path,
            "r",
            encoding="utf-8",
        ) as file:
            review = json.load(file)

        if review.get("analysis_id") != analysis_id:
            return None

        return review

    def list_ai_review_history(self):
        if not os.path.isdir(self.ai_review_history_dir):
            return []

        archives = []

        for filename in os.listdir(self.ai_review_history_dir):
            if not filename.endswith(".json"):
                continue

            archive_path = os.path.join(
                self.ai_review_history_dir,
                filename,
            )

            try:
                with open(
                    archive_path,
                    "r",
                    encoding="utf-8",
                ) as file:
                    review = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            analysis_id = review.get("analysis_id")

            if not analysis_id:
                continue

            archives.append(
                {
                    "analysis_id": analysis_id,
                    "source_filename": review.get(
                        "source_filename"
                    ),
                    "decision": review.get("decision"),
                    "archived_at": review.get("archived_at"),
                    "history_event_count": len(
                        review.get(
                            "excluded_fact_review_history",
                            [],
                        )
                    ),
                }
            )

        archives.sort(
            key=lambda item: item.get("archived_at") or "",
            reverse=True,
        )
        return archives

    def get_ai_analysis(self):

        if not os.path.exists(self.ai_file_path):
            return None

        with open(
            self.ai_file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)


    def get_analysis(self):

        if not os.path.exists(self.file_path):
            return None

        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)


project_service = ProjectService()
