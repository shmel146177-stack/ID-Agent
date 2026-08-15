import json
from datetime import datetime
from pathlib import Path

from app.services.hidden_works_registry import hidden_works_registry


class SupportingDocumentsRegistry:
    """
    Формирование предварительного реестра
    сопроводительной исполнительной документации.

    Версия v6.62.

    На основании найденных АОСР определяются
    потенциально необходимые:

    04 - исполнительные схемы;
    05 - протоколы и испытания;
    06 - паспорта и сертификаты.

    Важно:
    наличие требования в реестре не означает,
    что документ фактически существует.

    Каждый документ должен быть подтверждён
    реальным файлом и инженерной проверкой.
    """

    REQUIREMENTS = {
        "grounding_device": [
            {
                "code": "grounding_executive_scheme",
                "section_code": "executive_schemes",
                "section_number": "04",
                "section_title": "Исполнительные схемы",
                "title": ("Исполнительная схема " "заземляющего устройства"),
                "document_types": ["\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"],
                "match_keywords": [
                    "\u0437\u0430\u0437\u0435\u043c\u043b",
                ],
                "priority": "Высокий",
                "reason": (
                    "Для подтверждения фактического "
                    "расположения заземляющих электродов, "
                    "проводников, соединений и привязок."
                ),
            },
            {
                "code": "grounding_resistance_protocol",
                "section_code": "tests",
                "section_number": "05",
                "section_title": "Протоколы и испытания",
                "title": (
                    "Протокол измерения сопротивления " "заземляющего устройства"
                ),
                "document_types": ["\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b"],
                "match_keywords": [
                    "\u0441\u043e\u043f\u0440\u043e\u0442\u0438\u0432\u043b\u0435\u043d",
                    "\u0437\u0430\u0437\u0435\u043c\u043b",
                ],
                "priority": "Высокий",
                "reason": (
                    "Для подтверждения результатов "
                    "измерений фактически выполненного "
                    "заземляющего устройства."
                ),
            },
            {
                "code": "grounding_quality_documents",
                "section_code": "quality_documents",
                "section_number": "06",
                "section_title": "Паспорта и сертификаты",
                "title": ("Документы качества на материалы " "заземляющего устройства"),
                "document_types": ["\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f", "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442", "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f"],
                "match_any_keywords": [
                    "\u0437\u0430\u0437\u0435\u043c\u043b",
                    "\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0434",
                    "\u043f\u043e\u043b\u043e\u0441",
                    "\u043f\u0440\u043e\u0432\u043e\u0434\u043d\u0438\u043a",
                    "\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u0435\u043b",
                ],
                "priority": "Высокий",
                "reason": (
                    "Для подтверждения характеристик "
                    "фактически применённых электродов, "
                    "полосы, проводников и соединительных "
                    "элементов."
                ),
            },
        ],
        "cable_entry": [
            {
                "code": "cable_entry_executive_scheme",
                "section_code": "executive_schemes",
                "section_number": "04",
                "section_title": "Исполнительные схемы",
                "title": ("Исполнительная схема " "кабельного ввода"),
                "document_types": ["\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"],
                "match_keywords": [
                    "\u043a\u0430\u0431\u0435\u043b\u044c\u043d",
                    "\u0432\u0432\u043e\u0434",
                ],
                "priority": "Высокий",
                "reason": (
                    "Для фиксации фактической трассы, "
                    "проходок, футляров, защитных труб "
                    "и привязок кабельного ввода."
                ),
            },
            {
                "code": "cable_test_protocol",
                "section_code": "tests",
                "section_number": "05",
                "section_title": "Протоколы и испытания",
                "title": ("Протокол испытаний или измерений " "кабельной линии"),
                "document_types": ["\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b"],
                "match_keywords": [
                    "\u043a\u0430\u0431\u0435\u043b\u044c\u043d",
                ],
                "priority": "Средний",
                "reason": (
                    "Необходимость и состав испытаний "
                    "должны быть уточнены по фактической "
                    "кабельной линии, проекту и требованиям "
                    "приёмки."
                ),
            },
            {
                "code": "cable_quality_documents",
                "section_code": "quality_documents",
                "section_number": "06",
                "section_title": "Паспорта и сертификаты",
                "title": (
                    "Документы качества на кабель, "
                    "защитные трубы и элементы проходок"
                ),
                "document_types": ["\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f", "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442", "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f"],
                "match_any_keywords": [
                    "\u043a\u0430\u0431\u0435\u043b",
                    "\u0442\u0440\u0443\u0431",
                    "\u043f\u0440\u043e\u0445\u043e\u0434",
                ],
                "priority": "Высокий",
                "reason": (
                    "Для подтверждения характеристик "
                    "фактически применённых материалов "
                    "кабельного ввода."
                ),
            },
        ],
        "support_foundations": [
            {
                "code": "supports_executive_scheme",
                "section_code": "executive_schemes",
                "section_number": "04",
                "section_title": "Исполнительные схемы",
                "title": ("Исполнительная схема " "расположения временных опор"),
                "document_types": ["\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"],
                "match_keywords": [
                    "\u0440\u0430\u0441\u043f\u043e\u043b\u043e\u0436",
                    "\u043e\u043f\u043e\u0440",
                ],
                "priority": "Средний",
                "reason": (
                    "Для фиксации фактического положения "
                    "опор и скрытых элементов оснований."
                ),
            },
            {
                "code": "supports_quality_documents",
                "section_code": "quality_documents",
                "section_number": "06",
                "section_title": "Паспорта и сертификаты",
                "title": (
                    "Документы качества на материалы "
                    "оснований и элементов временных опор"
                ),
                "document_types": ["\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f", "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442", "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f"],
                "match_any_keywords": [
                    "\u043e\u043f\u043e\u0440",
                    "\u0444\u0443\u043d\u0434\u0430\u043c\u0435\u043d\u0442",
                ],
                "priority": "Средний",
                "reason": (
                    "Требуется подтвердить фактически "
                    "применённые материалы, если такие "
                    "документы предусмотрены для "
                    "использованных изделий."
                ),
            },
        ],
    }

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

    def _copy_evidence(
        self,
        act: dict,
    ) -> list[dict]:

        result = []

        for item in act.get(
            "evidence",
            [],
        ):

            result.append(
                {
                    "sheet_number": (item.get("sheet_number")),
                    "title": (item.get("title")),
                    "page_type": (item.get("page_type")),
                    "pages_count": (item.get("pages_count")),
                    "source": (item.get("source")),
                }
            )

        return result

    def _build_requirement(
        self,
        act: dict,
        requirement: dict,
    ) -> dict:

        return {
            "code": (requirement["code"]),
            "section_code": (requirement["section_code"]),
            "section_number": (requirement["section_number"]),
            "section_title": (requirement["section_title"]),
            "title": (requirement["title"]),
            "status": ("Ожидает документа"),
            "priority": (requirement["priority"]),
            "confirmation_required": (True),
            "reason": (requirement["reason"]),
            "source_act": {
                "code": (act.get("code")),
                "title": (act.get("act_title") or act.get("title")),
            },
            "evidence": (self._copy_evidence(act)),
        }

    def _deduplicate(
        self,
        requirements: list[dict],
    ) -> list[dict]:

        result = []
        seen = set()

        for item in requirements:

            code = item.get("code")

            if code in seen:
                continue

            seen.add(code)

            result.append(item)

        return result

    def _build_sections(
        self,
        requirements: list[dict],
    ) -> list[dict]:

        section_definitions = [
            {
                "number": "04",
                "code": "executive_schemes",
                "title": "Исполнительные схемы",
            },
            {
                "number": "05",
                "code": "tests",
                "title": "Протоколы и испытания",
            },
            {
                "number": "06",
                "code": "quality_documents",
                "title": "Паспорта и сертификаты",
            },
        ]

        sections = []

        for section in section_definitions:

            documents = [
                item
                for item in requirements
                if (item.get("section_code") == section["code"])
            ]

            high_priority_count = sum(
                1 for item in documents if (item.get("priority") == "Высокий")
            )

            sections.append(
                {
                    "number": (section["number"]),
                    "code": (section["code"]),
                    "title": (section["title"]),
                    "status": (
                        "Ожидает документов"
                        if documents
                        else ("Требования " "автоматически " "не определены")
                    ),
                    "required_count": (len(documents)),
                    "high_priority_count": (high_priority_count),
                    "documents": (documents),
                }
            )

        return sections

    def analyze_project(
        self,
        project_name: str,
    ) -> dict:

        project_path = self._project_path(project_name)

        if not project_path.exists():

            raise FileNotFoundError(("Проект не найден: " f"{project_name}"))

        # ---------------------------------------------------------
        # 1. ПОЛУЧАЕМ ПРЕДВАРИТЕЛЬНЫЙ РЕЕСТР АОСР
        # ---------------------------------------------------------

        hidden_works = hidden_works_registry.analyze_project(project_name)

        requirements = []

        # ---------------------------------------------------------
        # 2. ОПРЕДЕЛЯЕМ СОПРОВОДИТЕЛЬНЫЕ ДОКУМЕНТЫ
        # ---------------------------------------------------------

        for act in hidden_works.get(
            "acts",
            [],
        ):

            act_code = act.get("code")

            rule_requirements = self.REQUIREMENTS.get(
                act_code,
                [],
            )

            for requirement in rule_requirements:

                requirements.append(
                    self._build_requirement(
                        act,
                        requirement,
                    )
                )

        requirements = self._deduplicate(requirements)

        # ---------------------------------------------------------
        # 3. ГРУППИРУЕМ ПО РАЗДЕЛАМ 04 / 05 / 06
        # ---------------------------------------------------------

        sections = self._build_sections(requirements)

        high_priority_count = sum(
            1 for item in requirements if (item.get("priority") == "Высокий")
        )

        result = {
            "project": (project_name),
            "created_at": (datetime.now().isoformat(timespec="seconds")),
            "status": (
                "Сформирован " "предварительный перечень"
                if requirements
                else ("Сопроводительные документы " "автоматически не определены")
            ),
            "method": ("Анализ предварительного реестра " "АОСР и проектных оснований"),
            "requirements_count": (len(requirements)),
            "high_priority_count": (high_priority_count),
            "requires_field_confirmation": (bool(requirements)),
            "sections": (sections),
            "requirements": (requirements),
            "note": (
                "Перечень сформирован автоматически. "
                "Он не подтверждает наличие документа "
                "и не заменяет требования проекта, "
                "приёмки или инженерной проверки. "
                "Каждая позиция должна быть подтверждена "
                "реальным документом."
            ),
        }

        # ---------------------------------------------------------
        # 4. СОХРАНЯЕМ JSON
        # ---------------------------------------------------------

        analysis_folder = self._analysis_path(project_name)

        analysis_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = analysis_folder / "supporting_documents_registry.json"

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


supporting_documents_registry = SupportingDocumentsRegistry()
