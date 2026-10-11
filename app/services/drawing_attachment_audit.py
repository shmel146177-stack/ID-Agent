"""Conservative comparison of attached-document registers with PDF stamps."""

import re
from pathlib import Path

import fitz

from app.services.safe_paths import safe_project_path


class DrawingAttachmentAudit:
    DESIGNATION = re.compile(
        r"\d{3,}/\d{2,4}-[А-ЯA-Z]{1,4}\.[А-ЯA-Z]+\d*", re.IGNORECASE
    )

    @staticmethod
    def _normalize_designation_text(text: str) -> str:
        return text.replace("\u00ad", "-").replace("‐", "-").replace("‑", "-")

    @staticmethod
    def _registered_designations(page: fitz.Page) -> list[str]:
        bounds = page.rect
        # The attached-document table occupies the right side of these registers.
        region = fitz.Rect(bounds.width * 0.5, 0, bounds.width, bounds.height * 0.55)
        text = DrawingAttachmentAudit._normalize_designation_text(
            page.get_text(clip=region, sort=True)
        )
        marker = text.lower().find("прилагаемые документы")
        if marker < 0:
            return []
        return list(
            dict.fromkeys(
                match.group()
                for match in DrawingAttachmentAudit.DESIGNATION.finditer(text[marker:])
            )
        )

    @classmethod
    def _stamp_designation(cls, page: fitz.Page) -> str | None:
        bounds = page.rect
        words = page.get_text(
            "words",
            clip=fitz.Rect(0, bounds.height * 0.65, bounds.width, bounds.height),
        )
        candidates = [
            (word[1], cls._normalize_designation_text(word[4].strip(".,;")))
            for word in words
            if cls.DESIGNATION.fullmatch(
                cls._normalize_designation_text(word[4].strip(".,;"))
            )
        ]
        return max(candidates)[1] if candidates else None

    @staticmethod
    def _declared_sheet_count(page: fitz.Page) -> int | None:
        bounds = page.rect
        words = page.get_text(
            "words",
            clip=fitz.Rect(0, bounds.height * 0.65, bounds.width, bounds.height),
        )
        headers = [word for word in words if word[4].lower() == "листов"]
        if not headers:
            return None
        header = max(headers, key=lambda word: (word[1], word[0]))
        values = [
            word
            for word in words
            if word[4].isdigit()
            and header[3] <= word[1] <= header[3] + 45
            and header[0] - 12 <= (word[0] + word[2]) / 2 <= header[2] + 12
        ]
        if not values:
            return None
        value = min(values, key=lambda word: word[1] - header[3])
        return int(value[4])

    def analyze(self, project_name: str, drawing_register: dict) -> dict:
        project_path = safe_project_path(project_name)
        details = []
        warnings = []
        unchecked = []
        seen = set()

        for register in drawing_register.get("registers", []):
            filename = register.get("filename")
            register_page = register.get("page")
            if not isinstance(filename, str) or Path(filename).name != filename:
                unchecked.append({"filename": filename, "reason": "invalid_filename"})
                continue
            source_path = project_path / "input" / filename
            if not source_path.is_file():
                unchecked.append(
                    {"filename": filename, "reason": "source_pdf_unavailable"}
                )
                continue
            try:
                with fitz.open(source_path) as pdf:
                    if type(register_page) is not int or not 1 <= register_page <= len(
                        pdf
                    ):
                        unchecked.append(
                            {"filename": filename, "reason": "invalid_register_page"}
                        )
                        continue
                    expected = self._registered_designations(pdf[register_page - 1])
                    if not expected:
                        unchecked.append(
                            {
                                "filename": filename,
                                "reason": "attached_register_unreadable_or_absent",
                            }
                        )
                        continue
                    observed = {}
                    for page_number in range(register_page + 1, len(pdf) + 1):
                        designation = self._stamp_designation(pdf[page_number - 1])
                        if designation:
                            observed.setdefault(designation, []).append(page_number)

                    for designation in expected:
                        key = (filename, designation)
                        if key in seen:
                            continue
                        seen.add(key)
                        pages = observed.get(designation, [])
                        suffix = designation.rsplit("-", 1)[-1]
                        candidates = [
                            code
                            for code in observed
                            if code not in expected
                            and code.rsplit("-", 1)[-1] == suffix
                        ]
                        detail = {
                            "filename": filename,
                            "register_page": register_page,
                            "expected_designation": designation,
                            "observed_designation": designation if pages else None,
                            "pages": pages,
                            "declared_sheets": None,
                        }
                        if pages:
                            total = self._declared_sheet_count(pdf[pages[0] - 1])
                            detail["declared_sheets"] = total
                            if total is None:
                                unchecked.append(
                                    {
                                        "filename": filename,
                                        "expected_designation": designation,
                                        "reason": "sheet_count_unreadable",
                                    }
                                )
                            elif total != len(pages):
                                warnings.append(
                                    {
                                        "code": "sheet_count_mismatch",
                                        "filename": filename,
                                        "register_page": register_page,
                                        "expected_designation": designation,
                                        "observed_designation": designation,
                                        "pages": pages,
                                        "declared_sheets": total,
                                        "observed_pages": len(pages),
                                        "message": (
                                            f"{designation}: в первом штампе листов {total}, "
                                            f"страниц с этим шифром {len(pages)} "
                                            f"(PDF {', '.join(map(str, pages))})"
                                        ),
                                        "engineer_confirmation_required": True,
                                    }
                                )
                        elif len(candidates) == 1:
                            candidate = candidates[0]
                            detail["observed_designation"] = candidate
                            detail["pages"] = observed[candidate]
                            warnings.append(
                                {
                                    "code": "designation_mismatch_candidate",
                                    "filename": filename,
                                    "register_page": register_page,
                                    "expected_designation": designation,
                                    "observed_designation": candidate,
                                    "pages": observed[candidate],
                                    "message": (
                                        f"Ведомость: {designation}; кандидат в штампе: "
                                        f"{candidate} (PDF "
                                        f"{', '.join(map(str, observed[candidate]))})"
                                    ),
                                    "engineer_confirmation_required": True,
                                }
                            )
                        else:
                            unchecked.append(
                                {
                                    "filename": filename,
                                    "expected_designation": designation,
                                    "reason": "matching_stamp_not_found",
                                }
                            )
                        details.append(detail)
            except (OSError, RuntimeError, ValueError):
                unchecked.append(
                    {"filename": filename, "reason": "source_pdf_unreadable"}
                )

        return {
            "status": (
                "warnings"
                if warnings
                else "not_checked" if unchecked else "no_warnings"
            ),
            "documents": details,
            "warnings": warnings,
            "unchecked": unchecked,
        }


drawing_attachment_audit = DrawingAttachmentAudit()
