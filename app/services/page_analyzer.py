import re


class PageAnalyzer:
    """Классификация отдельных страниц проектной документации."""

    def __init__(self):

        self.rules = {
            "Технические условия": {
                "технические условия": 25,
                "технологическое присоединение": 15,
                "максимальная мощность": 10,
                "точка присоединения": 10,
                "точки присоединения": 10,
                "россети московский регион": 8,
                "энергопринимающих устройств": 6,
            },
            "Согласование": {
                "согласование": 20,
                "согласовано": 20,
                "письмо": 8,
                "исх.": 6,
                "департамент": 5,
                "государственное бюджетное учреждение": 5,
                "автомобильные дороги": 12,
                "жилищник ярославского района": 12,
            },
            "Ведомость рабочих чертежей": {
                "ведомость рабочих чертежей": 20,
                "ведомость ссылочных и прилагаемых документов": 8,
                "ссылочные документы": 4,
            },
            "Ситуационный план": {
                "ситуационный план": 20,
                "м 1:2000": 5,
            },
            "Заземление": {
                "заземление": 12,
                "заземлитель": 10,
                "контур заземления": 15,
                "очаг заземления": 15,
                "система заземления": 15,
                "заземляющ": 8,
            },
            "Узел монтажа": {
                "узел монтажа": 20,
                "узел ввода": 12,
                "монтаж": 4,
            },
            "Спецификация": {
                "спецификация оборудования": 20,
                "наименование и техническая характеристика": 15,
                "поставщик": 8,
                "ед. измерения": 6,
                "кол-во": 5,
                "масса ед": 5,
                "поз. обозначение наименование": 8,
            },
            "Электрическая схема": {
                "электрическая схема": 20,
                "однолинейная схема": 20,
                "принципиальная схема": 20,
                "граница бп и эо": 10,
                "приборы учета": 8,
                "меркурий": 5,
                "расчетный ток": 6,
                "вводной выключатель": 6,
                "аппарат отходящей линии": 6,
                "ру-0,4 кв": 5,
                "врщ-0,4кв": 5,
            },
            "План электроснабжения": {
                "проектируемая вл": 12,
                "прокладывается по существующим опорам": 12,
                "кабельная линия": 8,
                "ввод в тп": 8,
                "стройгенплан": 8,
                "сип 2а": 5,
                "апвббшп": 5,
                "наружные сети электроснабжения": 5,
            },
            "Охрана окружающей среды": {
                "охрана окружающей среды": 20,
            },
            "Общие данные": {
                "общие данные": 15,
                "общие указания": 10,
                "рабочая документация": 3,
                "технические условия": 3,
            },
            "Титульный лист": {
                "рабочая документация": 8,
                "том 1": 8,
                "генеральный директор": 6,
                "наружные сети электроснабжения": 4,
            },
        }

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

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _preview(
        self,
        text: str,
        limit: int = 180,
    ) -> str:

        clean_text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if len(clean_text) <= limit:
            return clean_text

        return clean_text[:limit].rstrip() + "..."

    def _detect_priority_type(
        self,
        normalized_text: str,
        is_drawing: bool = False,
    ) -> str | None:
        """
        Определяет тип страницы по явным заголовкам
        и характерным признакам.
        """

        # ---------------------------------------------------------
        # ТЕХНИЧЕСКИЕ УСЛОВИЯ
        # ---------------------------------------------------------

        if not is_drawing and ("технические условия" in normalized_text or (
            "технологическое присоединение" in normalized_text
            and "россети московский регион" in normalized_text
        )):
            return "Технические условия"

        # ---------------------------------------------------------
        # СОГЛАСОВАНИЯ / ОФИЦИАЛЬНЫЕ ПИСЬМА
        # ---------------------------------------------------------

        approval_organizations = (
            "автомобильные дороги",
            "жилищник ярославского района",
        )

        if not is_drawing and any(
            organization in normalized_text for organization in approval_organizations
        ):
            return "Согласование"

        if not is_drawing and "государственное бюджетное учреждение" in normalized_text and (
            "согласован" in normalized_text
            or "письмо" in normalized_text
            or "исх." in normalized_text
        ):
            return "Согласование"

        # ---------------------------------------------------------
        # ЯВНЫЕ ЗАГОЛОВКИ
        # ---------------------------------------------------------

        if is_drawing:
            if "ведомость рабочих чертежей" in normalized_text:
                return "Ведомость рабочих чертежей"
            if "общие данные" in normalized_text:
                return "Общие данные"
            if re.search(r"план (?:выноса|прокладки) (?:кл|кабельн)", normalized_text):
                return "План электроснабжения"

        priority_rules = [
            (
                "Ведомость рабочих чертежей",
                [
                    "ведомость рабочих чертежей",
                ],
            ),
            (
                "Ситуационный план",
                [
                    "ситуационный план",
                ],
            ),
            (
                "Охрана окружающей среды",
                [
                    "охрана окружающей среды",
                ],
            ),
            (
                "Узел монтажа",
                [
                    "узел монтажа",
                ],
            ),
            (
                "Спецификация",
                [
                    "спецификация оборудования",
                    "наименование и техническая характеристика",
                ],
            ),
            (
                "Заземление",
                [
                    "очаг заземления",
                    "система заземления",
                    "контур заземления",
                ],
            ),
            (
                "Электрическая схема",
                [
                    "однолинейная схема",
                    "принципиальная схема",
                    "электрическая схема",
                ],
            ),
        ]

        for page_type, phrases in priority_rules:

            for phrase in phrases:

                if phrase in normalized_text:
                    return page_type

        return None

    def analyze_page(
        self,
        text: str,
        page_number: int | None = None,
    ) -> dict:

        text = text or ""

        if not text.strip():

            return {
                "page": page_number,
                "page_type": "Требуется OCR",
                "score": 0,
                "text_length": 0,
                "preview": "",
            }

        normalized_text = self._normalize(text)
        # A title block is evidence of a drawing; its approval/signature labels
        # are not evidence that the page is an approval letter.
        is_drawing = (
            "стадия" in normalized_text
            and "лист" in normalized_text
            and sum(label in normalized_text for label in
                    ("разработал", "проверил", "гип", "подпись", "инв.")) >= 2
        )

        # ---------------------------------------------------------
        # 1. ЯВНЫЕ ПРИЗНАКИ
        # ---------------------------------------------------------

        priority_type = self._detect_priority_type(normalized_text, is_drawing=is_drawing)

        if priority_type:

            return {
                "page": page_number,
                "page_type": priority_type,
                "score": 100,
                "text_length": len(text),
                "preview": self._preview(text),
            }

        # ---------------------------------------------------------
        # 2. ОЦЕНКА ПО КЛЮЧЕВЫМ СЛОВАМ
        # ---------------------------------------------------------

        scores = {}

        for page_type, rules in self.rules.items():
            if is_drawing and page_type in {"Согласование", "Технические условия", "Титульный лист"}:
                continue

            score = 0

            for phrase, weight in rules.items():

                normalized_phrase = self._normalize(phrase)

                occurrences = normalized_text.count(normalized_phrase)

                if occurrences:

                    occurrences = min(
                        occurrences,
                        3,
                    )

                    score += weight * occurrences

            scores[page_type] = score

        best_type = max(
            scores,
            key=scores.get,
        )

        best_score = scores[best_type]

        # ---------------------------------------------------------
        # 3. ТИТУЛЬНЫЕ ЛИСТЫ
        # ---------------------------------------------------------

        if (
            page_number
            and page_number <= 3
            and "рабочая документация" in normalized_text
        ):

            title_score = scores.get(
                "Титульный лист",
                0,
            )

            if title_score >= 8:
                best_type = "Титульный лист"
                best_score = title_score

        if best_score < 5:
            best_type = "Рабочий чертеж" if is_drawing else "Не определено"

        return {
            "page": page_number,
            "page_type": best_type,
            "score": best_score,
            "text_length": len(text),
            "preview": self._preview(text),
        }


page_analyzer = PageAnalyzer()
