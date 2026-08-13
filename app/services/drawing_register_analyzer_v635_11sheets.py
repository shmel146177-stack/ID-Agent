import re


class DrawingRegisterAnalyzer:
    """
    Анализатор ведомости рабочих чертежей.

    Основная задача:
    - найти именно нумерованный блок ведомости;
    - извлечь названия листов в правильном порядке;
    - восстановить номера листов по последовательности;
    - явно указать, что номер восстановлен, а не напрямую прочитан.
    """

    REGISTER_MARKERS = (
        "ведомость рабочих чертежей",
        "ведомость рабочих чертежей основного комплекта",
    )

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
            (r"\bкомпоновка\b.*\bврщ\b.*\bаб",),
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
            (r"\bкомпоновка\b.*\bврщ\b.*\bтерритор",),
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
    ]

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

        # Частая ошибка исходного PDF.
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

        lines = []

        for raw_line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                raw_line,
            ).strip()

            if line:
                lines.append(line)

        return lines

    def _is_register(
        self,
        text: str,
    ) -> bool:

        normalized = self._normalize(text)

        return any(marker in normalized for marker in self.REGISTER_MARKERS)

    def _is_number_line(
        self,
        line: str,
    ) -> bool:

        value = line.strip()

        if not re.fullmatch(
            r"\d{1,2}",
            value,
        ):
            return False

        number = int(value)

        return 1 <= number <= 99

    def _match_title(
        self,
        line: str,
    ) -> str | None:

        normalized = self._normalize(line)

        if not normalized:
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

    def _find_register_block_start(
        self,
        lines: list[str],
    ) -> int | None:
        """
        В PDF фраза "Общие данные" может встречаться несколько раз.

        Выбираем то вхождение, после которого имеется
        значительное количество отдельных номеров листов.
        """

        candidates = []

        for index, line in enumerate(lines):

            if self._normalize(line) != "общие данные":
                continue

            end_index = min(
                len(lines),
                index + 80,
            )

            number_count = sum(
                1
                for candidate_line in lines[index:end_index]
                if self._is_number_line(candidate_line)
            )

            title_count = sum(
                1
                for candidate_line in lines[index:end_index]
                if self._match_title(candidate_line)
            )

            candidates.append(
                {
                    "index": index,
                    "number_count": (number_count),
                    "title_count": (title_count),
                }
            )

        if not candidates:
            return None

        # Ищем блок, где одновременно много номеров
        # и много названий листов.
        best = max(
            candidates,
            key=lambda item: (
                item["number_count"],
                item["title_count"],
                item["index"],
            ),
        )

        if best["number_count"] < 5 or best["title_count"] < 5:
            return None

        return best["index"]

    def _extract_register_block(
        self,
        lines: list[str],
    ) -> list[str]:

        start_index = self._find_register_block_start(lines)

        if start_index is None:
            return []

        block = []

        for line in lines[start_index:]:

            normalized = self._normalize(line)

            # После ведомости обычно начинается
            # штамп рабочего листа.
            if block and normalized in {
                "инв. n° подл.",
                "инв. № подл.",
                "инв. n подл.",
            }:
                break

            block.append(line)

            # Для обычного основного комплекта
            # больше 100 строк нам здесь не требуется.
            if len(block) >= 100:
                break

        return block

    def _extract_titles(
        self,
        block: list[str],
    ) -> list[dict]:

        entries = []

        seen = set()

        for line in block:

            title = self._match_title(line)

            if not title:
                continue

            if title in seen:
                continue

            seen.add(title)

            entries.append(
                {
                    "title": title,
                    "source_line": line,
                }
            )

        return entries

    def _extract_number_evidence(
        self,
        block: list[str],
    ) -> list[int]:

        numbers = []

        for line in block:

            if not self._is_number_line(line):
                continue

            number = int(line.strip())

            if number not in numbers:
                numbers.append(number)

        return numbers

    def _can_restore_sequence(
        self,
        entries: list[dict],
        number_evidence: list[int],
    ) -> bool:
        """
        Разрешаем восстановление последовательности,
        только если PDF содержит достаточно числовых
        признаков и список выглядит как ведомость.
        """

        entries_count = len(entries)

        if entries_count < 3:
            return False

        if len(number_evidence) < 3:
            return False

        expected_numbers = set(
            range(
                1,
                entries_count + 1,
            )
        )

        detected_numbers = set(number_evidence)

        matches = len(expected_numbers & detected_numbers)

        # Требуем подтверждения хотя бы примерно
        # половины ожидаемой последовательности.
        minimum_matches = max(
            3,
            entries_count // 2,
        )

        return matches >= minimum_matches

    def analyze_text(
        self,
        text: str,
    ) -> dict:

        text = text or ""

        lines = self._prepare_lines(text)

        register_detected = self._is_register(text)

        block = self._extract_register_block(lines)

        if not block:

            return {
                "register_detected": (register_detected),
                "register_block_detected": (False),
                "entries_count": 0,
                "numbered_entries_count": 0,
                "numbering_restored": False,
                "number_evidence": [],
                "entries": [],
            }

        entries = self._extract_titles(block)

        number_evidence = self._extract_number_evidence(block)

        numbering_restored = self._can_restore_sequence(
            entries,
            number_evidence,
        )

        result_entries = []

        for index, entry in enumerate(
            entries,
            start=1,
        ):

            if numbering_restored:

                sheet_number = index
                number_source = "restored_sequence"

            else:

                sheet_number = None
                number_source = None

            result_entries.append(
                {
                    "sheet_number": (sheet_number),
                    "number_source": (number_source),
                    "title": (entry["title"]),
                    "source_line": (entry["source_line"]),
                }
            )

        numbered_entries_count = sum(
            1 for entry in result_entries if entry["sheet_number"] is not None
        )

        return {
            "register_detected": (register_detected),
            "register_block_detected": True,
            "entries_count": len(result_entries),
            "numbered_entries_count": (numbered_entries_count),
            "numbering_restored": (numbering_restored),
            "number_evidence": (number_evidence),
            "entries": result_entries,
        }


drawing_register_analyzer = DrawingRegisterAnalyzer()
