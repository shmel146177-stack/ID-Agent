import re


class DrawingRegisterAnalyzer:
    """
    Анализатор ведомости рабочих чертежей.

    Извлекает из текста страницы названия листов проекта.
    Номера листов определяются только тогда, когда номер
    расположен рядом с названием достаточно однозначно.
    """

    REGISTER_MARKERS = (
        "ведомость рабочих чертежей",
        "ведомость рабочих чертежей основного комплекта",
    )

    # Канонические названия листов и варианты,
    # которые могут встречаться после PDF/OCR.
    DRAWING_PATTERNS = [
        (
            "Общие данные",
            (r"\bобщие данные\b",),
        ),
        (
            "Технические условия",
            (
                r"\bтехнические условия\b",
                r"\bту\s+пао\b",
                r"\bту\s+[иi]-?\d",
            ),
        ),
        (
            "Ситуационный план",
            (r"\bситуационный план\b",),
        ),
        (
            "План строительства линий",
            (
                r"\bплан строительства\b.*\bлиний\b",
                r"\bплан строительства\b.*\bвл\b",
                r"\bплан строительства\b.*\bквл\b",
            ),
        ),
        (
            "Структурная схема электроснабжения",
            (r"\bструктурная схема электроснабжения\b",),
        ),
        (
            "Компоновка ВРЩ-0,4кВ абонента",
            (r"\bкомп[ао]новка\b.*\bврщ\b.*\bаб",),
        ),
        (
            "Узел монтажа ВРЩ-0,4кВ абонента",
            (r"\bузел монтажа\b.*\bврщ\b.*\bаб",),
        ),
        (
            "Однолинейная схема ВРЩ-0,4кВ территории",
            (r"\bоднолинейн\w*\b.*\bсхем\w*\b.*\bврщ\b",),
        ),
        (
            "Компоновка ВРЩ-0,4кВ территории",
            (r"\bкомп[ао]новка\b.*\bврщ\b.*\bтерритор",),
        ),
        (
            "Узел монтажа ВРЩ-0,4кВ территории",
            (r"\bузел монтажа\b.*\bврщ\b.*\bтерритор",),
        ),
        (
            "Узел заземления ВРЩ-0,4кВ",
            (r"\bузел заземления\b.*\bврщ\b",),
        ),
        (
            "Устройство очага заземления",
            (
                r"\bустройство очага заземления\b",
                r"\bочаг заземления\b",
            ),
        ),
        (
            "Узел ввода кабельной линии",
            (
                r"\bузел ввода кабельной линии\b",
                r"\bузел ввода\b.*\bкабель",
            ),
        ),
        (
            "Общий вид временных опор",
            (r"\bобщий вид временных опор\b",),
        ),
        (
            "Чертеж ограждения",
            (r"\bчертеж ограждения\b",),
        ),
        (
            "Спецификация оборудования",
            (r"\bспецификация оборудования\b",),
        ),
    ]

    NOISE_LINES = {
        "наименование",
        "стр.",
        "стр",
        "примечание",
        "номер",
        "дата",
        "лист",
        "листов",
        "стадия",
        "подпись",
        "формат",
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

        # Частые ошибки PDF/OCR.
        text = text.replace(
            "компановка",
            "компоновка",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _prepare_lines(
        self,
        text: str,
    ) -> list[str]:

        result = []

        for raw_line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                raw_line,
            ).strip()

            if not line:
                continue

            result.append(line)

        return result

    def _is_register(
        self,
        text: str,
    ) -> bool:

        normalized = self._normalize(text)

        return any(marker in normalized for marker in self.REGISTER_MARKERS)

    def _match_title(
        self,
        line: str,
    ) -> str | None:

        normalized = self._normalize(line)

        if not normalized:
            return None

        if normalized in self.NOISE_LINES:
            return None

        for (
            canonical_name,
            patterns,
        ) in self.DRAWING_PATTERNS:

            for pattern in patterns:

                if re.search(
                    pattern,
                    normalized,
                    re.IGNORECASE,
                ):
                    return canonical_name

        return None

    def _number_from_line(
        self,
        line: str,
    ) -> int | None:

        value = line.strip()

        if not re.fullmatch(
            r"\d{1,2}",
            value,
        ):
            return None

        number = int(value)

        if 1 <= number <= 99:
            return number

        return None

    def _find_near_number(
        self,
        lines: list[str],
        index: int,
    ) -> int | None:
        """
        Ищем номер непосредственно рядом с названием.

        Используется только консервативная проверка,
        чтобы не присвоить неправильный номер
        из-за сложного порядка текста PDF.
        """

        candidates = []

        if index > 0:

            previous_number = self._number_from_line(lines[index - 1])

            if previous_number is not None:
                candidates.append(previous_number)

        if index + 1 < len(lines):

            next_number = self._number_from_line(lines[index + 1])

            if next_number is not None:
                candidates.append(next_number)

        candidates = list(dict.fromkeys(candidates))

        if len(candidates) == 1:
            return candidates[0]

        return None

    def analyze_text(
        self,
        text: str,
    ) -> dict:

        text = text or ""

        lines = self._prepare_lines(text)

        register_detected = self._is_register(text)

        entries = []

        seen_titles = set()

        for index, line in enumerate(lines):

            title = self._match_title(line)

            if not title:
                continue

            # Одно название листа добавляем один раз.
            if title in seen_titles:
                continue

            seen_titles.add(title)

            sheet_number = self._find_near_number(
                lines,
                index,
            )

            entries.append(
                {
                    "sheet_number": (sheet_number),
                    "title": title,
                    "source_line": line,
                }
            )

        numbered_entries = sum(
            1 for entry in entries if entry["sheet_number"] is not None
        )

        return {
            "register_detected": (register_detected),
            "entries_count": len(entries),
            "numbered_entries_count": (numbered_entries),
            "entries": entries,
        }


drawing_register_analyzer = DrawingRegisterAnalyzer()
