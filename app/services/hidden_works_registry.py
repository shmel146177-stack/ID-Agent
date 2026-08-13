import json
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

    def _project_path(
        self,
        project_name: str,
    ) -> Path:

        return Path("projects") / project_name

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
                else "АОСР автоматически не определены"
            ),
            "method": ("Анализ ведомости рабочих чертежей " "и типов страниц проекта"),
            "acts_count": len(acts),
            "high_priority_count": (high_priority_count),
            "requires_field_confirmation": (bool(acts)),
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

