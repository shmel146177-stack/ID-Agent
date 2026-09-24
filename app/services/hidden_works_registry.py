from app.services.safe_paths import safe_project_path
import json
import re
from datetime import datetime
from pathlib import Path


class HiddenWorksRegistry:
    """
    Предварительное определение актов
    освидетельствования скрытых работ (АОСР)
    по проектной документации.

    Важно:
    наличие чертежа не означает, что работа
    фактически выполнена.

    Поэтому ID-Agent формирует перечень
    потенциально необходимых актов,
    которые должны быть подтверждены
    по факту производства работ.
    """

    RULES = [
        {
            "code": "grounding_device",
            "title": "Устройство заземляющего устройства",
            "act_title": ("АОСР на устройство " "заземляющего устройства"),
            "triggers": [
                "заземлен",
                "очаг зазем",
            ],
            "page_types": [
                "Заземление",
            ],
            "priority": "Высокий",
            "confidence": "Высокая",
            "reason": (
                "В проекте обнаружены чертежи "
                "заземления. Электроды и скрытые "
                "элементы заземляющего устройства "
                "необходимо освидетельствовать "
                "до засыпки или закрытия."
            ),
            "confirmation": (
                "Подтвердить фактическое устройство "
                "заземляющих электродов, полосы, "
                "соединений и последующую засыпку."
            ),
        },
        {
            "code": "cable_entry",
            "title": "Устройство кабельного ввода",
            "act_title": ("АОСР на устройство " "скрытых участков кабельного ввода"),
            "triggers": [
                "узел ввода кабельной линии",
            ],
            "page_types": [],
            "priority": "Высокий",
            "confidence": "Высокая",
            "reason": (
                "В ведомости рабочих чертежей " "обнаружен узел ввода кабельной линии."
            ),
            "confirmation": (
                "Проверить наличие скрытой прокладки, "
                "защитных труб, футляров, проходок, "
                "герметизации и других элементов, "
                "закрываемых последующими работами."
            ),
        },
        {
            "code": "support_foundations",
            "title": ("Основания и скрытые элементы " "временных опор"),
            "act_title": ("АОСР на устройство оснований " "и скрытых элементов опор"),
            "triggers": [
                "временных опор",
                "воздушных линий",
            ],
            "page_types": [],
            "priority": "Средний",
            "confidence": "Средняя",
            "reason": (
                "В проекте обнаружены воздушные линии "
                "и временные опоры. Акт требуется, "
                "если предусмотрены скрываемые "
                "основания, фундаменты, закладные "
                "или подземные части опор."
            ),
            "confirmation": (
                "Уточнить конструкцию опор и наличие "
                "элементов, которые будут скрыты "
                "после монтажа или обратной засыпки."
            ),
        },
    ]

    # Design quantities identify review candidates, not completed work or signed acts.
    WORK_REVIEW_RULES = [
        {
            "code": "cable_trench",
            "title": "Кабельная линия в траншее",
            "section": "АС",
            "items": {
                "1.3": "постели из песка для кабельной линии",
                "1.5": "укрытие кабельных линий защитными плитами",
            },
        },
        {
            "code": "foundation_base",
            "title": "Основание и армирование фундаментной плиты",
            "section": "АС",
            "items": {
                "2.3": "песчаной подсыпки",
                "2.8": "армирование фундаментной плиты",
            },
        },
        {
            "code": "foundation_waterproofing",
            "title": "Гидроизоляция подземных конструкций",
            "section": "АС",
            "items": {
                "2.5": "бетонной подготовки битумным праймером",
                "2.6": "бетонной подготовки битумной мастикой",
            },
        },
        {
            "code": "embedded_cable_pipes",
            "title": "Закладные трубы и заделка кабельных проходок",
            "section": "АС",
            "items": {
                "2.16": "укладка труб полимерных термостойких",
                "2.21": "заделка труб и пазух цементным раствором",
            },
        },
        {
            "code": "apron_layers",
            "title": "Скрываемые слои и армирование отмостки",
            "section": "АС",
            "items": {
                "2.36": "гидроизоляции горизонтальной",
                "2.39": "укладка сварной сетки",
            },
        },
    ]

    WORK_ITEM_PATTERN = re.compile(r"(?m)^\s*(\d+\.\d+)\.\s*")
    WORK_SECTION_PATTERN = re.compile(
        r"(?m)^\s*\d[\d/.-]*-(АС|ЭП)\.ВОР\s*$", re.IGNORECASE
    )

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return safe_project_path(project_name)

    def _analysis_path(
        self,
        project_name: str,
    ) -> Path:

        return self._project_path(project_name) / "analysis"

    def _load_json(
        self,
        path: Path,
    ) -> dict:

        if not path.exists():
            return {}

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def _normalize(
        self,
        text: str,
    ) -> str:

        return str(text).lower().replace("ё", "е").strip()

    def _extract_register_entries(
        self,
        project_name: str,
    ) -> list[dict]:

        path = self._analysis_path(project_name) / "drawing_register.json"

        data = self._load_json(path)

        entries = []

        top_entries = data.get(
            "entries",
            [],
        )

        if isinstance(
            top_entries,
            list,
        ):

            entries.extend(top_entries)

        for register in data.get(
            "registers",
            [],
        ):

            register_entries = register.get(
                "entries",
                [],
            )

            if isinstance(
                register_entries,
                list,
            ):

                entries.extend(register_entries)

        # Убираем дубли.
        unique_entries = []
        seen = set()

        for entry in entries:

            number = entry.get("sheet_number")

            title = entry.get("title") or entry.get("name") or ""

            key = (
                str(number),
                self._normalize(title),
            )

            if key in seen:
                continue

            seen.add(key)

            unique_entries.append(entry)

        return unique_entries

    def _load_page_types(
        self,
        project_name: str,
    ) -> dict:

        path = self._analysis_path(project_name) / "page_analysis.json"

        data = self._load_json(path)

        page_types = data.get(
            "page_types",
            {},
        )

        if (
            isinstance(
                page_types,
                dict,
            )
            and page_types
        ):

            return page_types

        result = {}

        for document in data.get(
            "documents",
            [],
        ):

            for page in document.get(
                "pages",
                [],
            ):

                page_type = page.get("page_type")

                if not page_type:
                    continue

                result[page_type] = (
                    result.get(
                        page_type,
                        0,
                    )
                    + 1
                )

        return result

    def _load_work_review_candidates(self, project_name: str) -> list[dict]:
        """Find project-backed work groups without proposing signed acts."""

        data = self._load_json(self._analysis_path(project_name) / "page_analysis.json")
        work_items_by_document = {}

        for document in data.get("documents", []):
            filename = document.get("filename", "")
            for page in document.get("pages", []):
                if self._normalize(page.get("page_type", "")) not in {
                    "ведомость объемов работ",
                }:
                    continue

                text = page.get("text") or ""
                section_match = self.WORK_SECTION_PATTERN.search(text)
                if not section_match:
                    continue

                section = section_match.group(1).upper()
                work_items = work_items_by_document.setdefault((filename, section), {})
                matches = list(self.WORK_ITEM_PATTERN.finditer(text))
                for index, match in enumerate(matches):
                    end = (
                        matches[index + 1].start()
                        if index + 1 < len(matches)
                        else len(text)
                    )
                    work_items[match.group(1)] = {
                        "text": self._normalize(
                            re.sub(r"\s+", " ", text[match.end() : end])
                        ),
                        "filename": filename,
                        "page": page.get("page"),
                    }

        candidates = []
        for rule in self.WORK_REVIEW_RULES:
            evidence = []
            for (filename, section), work_items in work_items_by_document.items():
                if section != rule["section"]:
                    continue

                document_evidence = []
                for number, phrase in rule["items"].items():
                    item = work_items.get(number)
                    if not item or self._normalize(phrase) not in item["text"]:
                        break
                    document_evidence.append(
                        {
                            "document": filename,
                            "page": item["page"],
                            "work_item": number,
                            "matched_phrase": phrase,
                        }
                    )
                else:
                    evidence.extend(document_evidence)

            if evidence:
                candidates.append(
                    {
                        "code": rule["code"],
                        "title": rule["title"],
                        "status": "Требует проверки по факту",
                        "confirmation_required": True,
                        "evidence": evidence,
                    }
                )

        return candidates

    def _find_register_evidence(
        self,
        entries: list[dict],
        triggers: list[str],
    ) -> list[dict]:

        evidence = []

        normalized_triggers = [self._normalize(trigger) for trigger in triggers]

        for entry in entries:

            title = entry.get("title") or entry.get("name") or ""

            normalized_title = self._normalize(title)

            matched = False

            for trigger in normalized_triggers:

                if trigger in normalized_title:
                    matched = True
                    break

            if not matched:
                continue

            evidence.append(
                {
                    "sheet_number": (entry.get("sheet_number")),
                    "title": title,
                    "source": ("Ведомость рабочих чертежей"),
                }
            )

        return evidence

    def _find_page_type_evidence(
        self,
        page_types: dict,
        required_types: list[str],
    ) -> list[dict]:

        evidence = []

        for required_type in required_types:

            count = page_types.get(
                required_type,
                0,
            )

            if not count:
                continue

            evidence.append(
                {
                    "page_type": (required_type),
                    "pages_count": count,
                    "source": ("Постраничный анализ"),
                }
            )

        return evidence

    def _analyze_rule(
        self,
        rule: dict,
        entries: list[dict],
        page_types: dict,
    ) -> dict | None:

        register_evidence = self._find_register_evidence(
            entries,
            rule["triggers"],
        )

        page_evidence = self._find_page_type_evidence(
            page_types,
            rule["page_types"],
        )

        if not register_evidence and not page_evidence:

            return None

        evidence = register_evidence + page_evidence

        return {
            "code": rule["code"],
            "title": rule["title"],
            "act_title": (rule["act_title"]),
            "status": ("Требует подтверждения"),
            "priority": (rule["priority"]),
            "confidence": (rule["confidence"]),
            "reason": (rule["reason"]),
            "confirmation_required": (True),
            "confirmation": (rule["confirmation"]),
            "evidence": evidence,
        }

    def analyze_project(
        self,
        project_name: str,
    ) -> dict:

        project_path = self._project_path(project_name)

        if not project_path.exists():

            raise FileNotFoundError("Проект не найден: " f"{project_name}")

        entries = self._extract_register_entries(project_name)

        page_types = self._load_page_types(project_name)
        review_candidates = self._load_work_review_candidates(project_name)

        acts = []

        for rule in self.RULES:

            act = self._analyze_rule(
                rule,
                entries,
                page_types,
            )

            if act is not None:

                acts.append(act)

        high_priority_count = sum(1 for act in acts if act.get("priority") == "Высокий")

        result = {
            "project": project_name,
            "created_at": (datetime.now().isoformat(timespec="seconds")),
            "status": (
                "Сформирован предварительный перечень"
                if acts
                else (
                    "Найдены работы для проверки; АОСР автоматически не определены"
                    if review_candidates
                    else "АОСР автоматически не определены"
                )
            ),
            "method": (
                "Анализ ведомости рабочих чертежей, "
                "типов страниц и ведомостей объемов работ"
            ),
            "acts_count": len(acts),
            "review_candidates_count": len(review_candidates),
            "review_candidates": review_candidates,
            "high_priority_count": (high_priority_count),
            "requires_field_confirmation": bool(acts or review_candidates),
            "acts": acts,
            "note": (
                "Перечень сформирован автоматически "
                "по проектной документации. "
                "Необходимость каждого АОСР должна "
                "быть подтверждена по фактическому "
                "составу и технологии выполненных работ."
            ),
        }

        analysis_folder = self._analysis_path(project_name)

        analysis_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = analysis_folder / "hidden_works_registry.json"

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        result["analysis_file"] = str(output_file)

        return result


hidden_works_registry = HiddenWorksRegistry()
