import json
import re
from pathlib import Path


class DrawingSheetMatcher:
    """
    Сопоставляет листы, заявленные в ведомости рабочих
    чертежей, с реальными страницами PDF.

    Источники:
    - drawing_register.json
    - page_analysis.json

    Результат:
    - drawing_sheet_match.json
    """

    MATCH_RULES = {
        "Общие данные": [
            ("общие данные", 80),
            ("общие указания", 20),
            ("ведомость рабочих чертежей", 20),
        ],
        "Технические условия": [
            ("технические условия", 70),
            ("технологическое присоединение", 30),
            ("россети московский регион", 15),
            ("максимальная мощность", 10),
        ],
        "План строительства линий": [
            ("план строительства воздушных линий", 80),
            ("план строительства квл", 80),
            ("план строительства вл", 70),
            ("м1 500", 10),
            ("сип 2а", 10),
        ],
        "Структурная схема электроснабжения": [
            ("структурная схема электроснабжения", 100),
            ("граница бп и эо", 15),
            ("россети московский регион", 10),
        ],
        "Компоновка ВРЩ-0,4кВ абонента": [
            ("компоновка врщ 0 4кв аб та", 100),
            ("врщ 0 4кв аб та", 30),
            ("установка приборов учета", 15),
        ],
        "Узел монтажа ВРЩ-0,4кВ абонента": [
            ("узел монтажа врщ 0 4кв аб та", 100),
            ("монтаж врщ 0 4кв аб", 70),
            ("врщ 0 4кв аб та", 20),
        ],
        "Однолинейная схема ВРЩ-0,4кВ территории": [
            ("однолинейная схема врщ 0 4кв территории", 100),
            ("однолинейная схема", 60),
            ("врщ 0 4кв территории", 20),
            ("вводной выключатель", 10),
        ],
        "Компоновка ВРЩ-0,4кВ территории": [
            ("компоновка врщ 0 4кв территории", 100),
            ("врщ 0 4кв территории", 30),
            ("fu1 fu3", 10),
        ],
        "Узел монтажа ВРЩ-0,4кВ территории": [
            ("узел монтажа врщ 0 4кв территории", 100),
            ("ст уголок 50х50х5", 20),
            ("бетон", 10),
        ],
        "Узел заземления ВРЩ-0,4кВ": [
            ("узел заземления врщ 0 4кв", 100),
            ("система заземления", 30),
            ("заземляющее устройство", 20),
        ],
        "Устройство очага заземления": [
            ("устройство очага заземления", 100),
            ("очаг заземления", 60),
            ("вертикальный заземлитель", 20),
        ],
        "Узел ввода кабельной линии": [
            ("узел ввода кабельной линии", 100),
            ("ввод кабеля", 30),
            ("гермоввод", 20),
            ("кабельный проход", 10),
        ],
        "Общий вид временных опор": [
            ("общий вид временных опор", 100),
            ("временная опора", 30),
        ],
        "Чертеж ограждения": [
            ("чертеж ограждения", 100),
            ("панель 3d", 20),
            ("оцинкованная калитка", 20),
            ("винтовая опора", 10),
        ],
    }

    PAGE_TYPE_BONUSES = {
        "Общие данные": {
            "Ведомость рабочих чертежей": 20,
            "Общие данные": 30,
        },
        "Технические условия": {
            "Технические условия": 40,
        },
        "План строительства линий": {
            "План электроснабжения": 20,
        },
        "Структурная схема электроснабжения": {
            "Электрическая схема": 20,
        },
        "Компоновка ВРЩ-0,4кВ абонента": {
            "Электрическая схема": 15,
        },
        "Узел монтажа ВРЩ-0,4кВ абонента": {
            "Узел монтажа": 20,
            "Электрическая схема": 10,
        },
        "Однолинейная схема ВРЩ-0,4кВ территории": {
            "Электрическая схема": 30,
        },
        "Компоновка ВРЩ-0,4кВ территории": {
            "Электрическая схема": 20,
        },
        "Узел монтажа ВРЩ-0,4кВ территории": {
            "Узел монтажа": 30,
        },
        "Узел заземления ВРЩ-0,4кВ": {
            "Заземление": 30,
        },
        "Устройство очага заземления": {
            "Заземление": 30,
        },
        "Узел ввода кабельной линии": {
            "Заземление": 5,
            "План электроснабжения": 10,
        },
        "Общий вид временных опор": {
            "План электроснабжения": 10,
        },
        "Чертеж ограждения": {
            "Спецификация": 10,
        },
    }

    MIN_MATCH_SCORE = 35

    def _normalize(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        text = text.lower()

        text = text.replace(
            "ё",
            "е",
        )

        text = text.replace(
            "–",
            "-",
        )

        text = text.replace(
            "—",
            "-",
        )

        # Ошибка исходного PDF.
        text = text.replace(
            "компановка",
            "компоновка",
        )

        # Приводим обозначения к форме,
        # удобной для сравнения.
        text = re.sub(
            r"[^0-9a-zа-я]+",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

    def _analysis_path(
        self,
        project_name: str,
        filename: str,
    ) -> Path:

        return self._project_path(project_name) / "analysis" / filename

    def _load_json(
        self,
        file_path: Path,
    ) -> dict:

        if not file_path.exists():

            raise FileNotFoundError(f"Не найден файл: {file_path}")

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def _load_register(
        self,
        project_name: str,
    ) -> dict:

        return self._load_json(
            self._analysis_path(
                project_name,
                "drawing_register.json",
            )
        )

    def _load_page_analysis(
        self,
        project_name: str,
    ) -> dict:

        return self._load_json(
            self._analysis_path(
                project_name,
                "page_analysis.json",
            )
        )

    def _collect_pages(
        self,
        page_analysis: dict,
    ) -> list[dict]:

        pages = []

        for document in page_analysis.get(
            "documents",
            [],
        ):

            filename = document.get("filename")

            for page in document.get(
                "pages",
                [],
            ):

                pages.append(
                    {
                        "filename": filename,
                        "page": page.get("page"),
                        "page_type": page.get("page_type"),
                        "source": page.get("source"),
                        "text": (page.get("text", "") or ""),
                        "preview": (page.get("preview", "") or ""),
                    }
                )

        return pages

    def _collect_register_entries(
        self,
        drawing_register: dict,
    ) -> list[dict]:

        entries = []

        seen = set()

        for register in drawing_register.get(
            "registers",
            [],
        ):

            for entry in register.get(
                "entries",
                [],
            ):

                key = (
                    entry.get("sheet_number"),
                    entry.get("title"),
                )

                if key in seen:
                    continue

                seen.add(key)

                entries.append(entry)

        entries.sort(
            key=lambda item: (
                item.get("sheet_number")
                if item.get("sheet_number") is not None
                else 9999
            )
        )

        return entries

    def _collect_register_pages(
        self,
        drawing_register: dict,
    ) -> set[int]:

        pages = set()

        for register in drawing_register.get(
            "registers",
            [],
        ):

            page_number = register.get("page")

            if isinstance(
                page_number,
                int,
            ):
                pages.add(page_number)

        return pages

    def _score_page(
        self,
        title: str,
        page: dict,
    ) -> tuple[int, list[str]]:

        text = self._normalize(page.get("text", ""))

        score = 0

        matched_phrases = []

        title_normalized = self._normalize(title)

        # Максимальный признак:
        # полное название листа найдено в тексте.
        if title_normalized and title_normalized in text:

            score += 120

            matched_phrases.append(title)

        for (
            phrase,
            weight,
        ) in self.MATCH_RULES.get(
            title,
            [],
        ):

            normalized_phrase = self._normalize(phrase)

            if normalized_phrase and normalized_phrase in text:

                score += weight

                matched_phrases.append(phrase)

        page_type = page.get("page_type")

        type_bonus = self.PAGE_TYPE_BONUSES.get(
            title,
            {},
        ).get(
            page_type,
            0,
        )

        score += type_bonus

        return (
            score,
            matched_phrases,
        )

    def _confidence(
        self,
        score: int,
    ) -> str:

        if score >= 100:
            return "Высокая"

        if score >= 60:
            return "Средняя"

        if score >= self.MIN_MATCH_SCORE:
            return "Низкая"

        return "Нет"

    def _match_entry(
        self,
        entry: dict,
        pages: list[dict],
        register_pages: set[int],
    ) -> dict:

        title = entry.get("title", "") or ""

        candidates = []

        for page in pages:

            page_number = page.get("page")

            # Страница ведомости содержит названия
            # почти всех листов и поэтому способна
            # давать ложные совпадения.
            #
            # Для "Общие данные" она является
            # допустимым кандидатом, поскольку
            # ведомость находится именно на этом листе.
            if title != "Общие данные" and page_number in register_pages:
                continue

            (
                score,
                matched_phrases,
            ) = self._score_page(
                title,
                page,
            )

            if score <= 0:
                continue

            candidates.append(
                {
                    "filename": (page.get("filename")),
                    "page": (page_number),
                    "page_type": (page.get("page_type")),
                    "source": (page.get("source")),
                    "score": score,
                    "matched_phrases": (matched_phrases),
                    "preview": (page.get("preview", "")),
                }
            )

        candidates.sort(
            key=lambda item: (
                item["score"],
                -(item["page"] or 0),
            ),
            reverse=True,
        )

        best = candidates[0] if candidates else None

        found = bool(best and best["score"] >= self.MIN_MATCH_SCORE)

        top_candidates = candidates[:3]

        result = {
            "sheet_number": (entry.get("sheet_number")),
            "number_source": (entry.get("number_source")),
            "title": title,
            "found": found,
            "status": ("Найден" if found else "Не найден"),
            "matched_page": None,
            "matched_filename": None,
            "matched_page_type": None,
            "matched_source": None,
            "score": 0,
            "confidence": "Нет",
            "matched_phrases": [],
            "candidates": (top_candidates),
        }

        if best:

            result["score"] = best["score"]

            result["confidence"] = self._confidence(best["score"])

            result["matched_phrases"] = best["matched_phrases"]

            if found:

                result["matched_page"] = best["page"]

                result["matched_filename"] = best["filename"]

                result["matched_page_type"] = best["page_type"]

                result["matched_source"] = best["source"]

        return result

    def analyze_project(
        self,
        project_name: str,
    ) -> dict:

        drawing_register = self._load_register(project_name)

        page_analysis = self._load_page_analysis(project_name)

        entries = self._collect_register_entries(drawing_register)

        pages = self._collect_pages(page_analysis)

        register_pages = self._collect_register_pages(drawing_register)

        matches = []

        for entry in entries:

            matches.append(
                self._match_entry(
                    entry,
                    pages,
                    register_pages,
                )
            )

        expected_count = len(matches)

        found_count = sum(1 for match in matches if match["found"])

        missing_count = expected_count - found_count

        completeness_percent = (
            round(
                (found_count / expected_count * 100),
                1,
            )
            if expected_count
            else 0.0
        )

        missing_sheets = [
            {
                "sheet_number": (match["sheet_number"]),
                "title": (match["title"]),
            }
            for match in matches
            if not match["found"]
        ]

        output_path = self._analysis_path(
            project_name,
            "drawing_sheet_match.json",
        )

        result = {
            "project": project_name,
            "status": (
                "Полный комплект листов"
                if (expected_count > 0 and missing_count == 0)
                else "Есть отсутствующие листы"
            ),
            "expected_count": (expected_count),
            "found_count": (found_count),
            "missing_count": (missing_count),
            "completeness_percent": (completeness_percent),
            "register_pages": sorted(register_pages),
            "missing_sheets": (missing_sheets),
            "matches": matches,
            "output_path": str(output_path),
        }

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return result


drawing_sheet_matcher = DrawingSheetMatcher()
