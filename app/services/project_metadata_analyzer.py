import re


class ProjectMetadataAnalyzer:
    """Извлечение основных реквизитов строительного проекта из текста PDF."""

    def _clean(self, value: str | None) -> str | None:
        if not value:
            return None

        value = value.replace("\u00ad", "")
        value = value.replace("\xa0", " ")
        value = re.sub(r"\s+", " ", value)
        value = value.strip(" \t\r\n:;_-")

        return value or None

    def _previous_text(
        self,
        lines: list[str],
        index: int,
        count: int = 2,
    ) -> str | None:
        """Берёт несколько содержательных строк перед названием поля."""

        values = []

        for pos in range(index - 1, max(-1, index - count - 1), -1):
            line = self._clean(lines[pos])

            if not line:
                continue

            # Отсекаем служебные строки штампа чертежа.
            if line.lower() in {
                "изм.",
                "лист",
                "листов",
                "подпись",
                "дата",
                "разработал",
                "проверил",
                "стадия",
            }:
                continue

            values.insert(0, line)

        if not values:
            return None

        return self._clean(" ".join(values))

    def _value_after_label(
        self,
        line: str,
        label_pattern: str,
    ) -> str | None:
        """Извлекает значение, если оно находится в той же строке после метки."""

        match = re.search(
            rf"{label_pattern}\s*:?\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if not match:
            return None

        return self._clean(match.group(1))

    def analyze_text(self, text: str) -> dict:
        result = {
            "object_name": None,
            "address": None,
            "customer": None,
            "contractor": None,
            "designer": None,
            "chief_engineer": None,
            "contract_number": None,
        }

        lines = text.splitlines()

        # ---------------------------------------------------------
        # Наименование объекта
        # ---------------------------------------------------------

        for index, line in enumerate(lines):
            if not re.search(r"наименование\s+объекта", line, re.IGNORECASE):
                continue

            # В некоторых PDF значение стоит после названия поля.
            value = self._value_after_label(
                line,
                r"наименование\s+объекта",
            )

            if value and len(value) > 15:
                # Наименование может продолжаться через несколько строк.
                for offset in range(1, 4):
                    if index + offset >= len(lines):
                        break

                    next_line = self._clean(lines[index + offset])

                    if not next_line:
                        continue

                    # Пропускаем рамки и другой графический мусор.
                    letters_count = sum(char.isalpha() for char in next_line)

                    if letters_count < 8:
                        continue

                    if next_line.lower() in {
                        "изм.",
                        "лист",
                        "листов",
                        "подпись",
                        "дата",
                        "разработал",
                        "проверил",
                    }:
                        continue

                    value = self._clean(f"{value} {next_line}")
                    break

                result["object_name"] = value
                break

            # В штампах значение часто находится перед надписью.
            value = self._previous_text(lines, index, count=2)

            if value and len(value) > 15:
                result["object_name"] = value
                break

        # ---------------------------------------------------------
        # Заказчик
        # ---------------------------------------------------------

        for index, line in enumerate(lines):
            if not re.search(r"^\s*заказчик\s*:?\s*$", line, re.IGNORECASE):
                continue

            value = self._previous_text(lines, index, count=1)

            if value and (
                "ООО" in value
                or "АО " in value
                or "ПАО " in value
                or "ИП " in value
                or "ГБУ " in value
            ):
                result["customer"] = value
                break

        # Если основной штамп не найден — используем альтернативное поле.
        if not result["customer"]:
            for line in lines:
                match = re.search(
                    r"организация\s+заказчика\s*:\s*(.+)",
                    line,
                    re.IGNORECASE,
                )

                if match:
                    result["customer"] = self._clean(match.group(1))
                    break

        # ---------------------------------------------------------
        # CONTRACTOR EXTRACTION

        for line in lines:
            match = re.search(
                r"(?:\u0433\u0435\u043d\u0435\u0440\u0430\u043b\u044c\u043d\w*"
                r"\s+\u043f\u043e\u0434\u0440\u044f\u0434\u0447\u0438\u043a|"
                r"\u043f\u043e\u0434\u0440\u044f\u0434\u043d\w*\s+"
                r"\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\w*|"
                r"\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\w*"
                r"\s+\u043f\u043e\u0434\u0440\u044f\u0434\u0447\u0438\u043a\u0430|"
                r"\u043f\u043e\u0434\u0440\u044f\u0434\u0447\u0438\u043a)"
                r"\s*:\s*(.+)",
                line,
                re.IGNORECASE,
            )

            if match:
                result["contractor"] = self._clean(
                    match.group(1)
                )
                break

        # CONTRACT NUMBER EXTRACTION

        for line in lines:
            match = re.search(
                r"(?:\u0434\u043e\u0433\u043e\u0432\u043e\u0440"
                r"(?:\s+\u043f\u043e\u0434\u0440\u044f\u0434\u0430)?|"
                r"\u043a\u043e\u043d\u0442\u0440\u0430\u043a\u0442)"
                r"\s*(?:\u2116|N(?:o)?\.?)\s*"
                r"([0-9A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451]"
                r"[0-9A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451./_-]*)",
                line,
                re.IGNORECASE,
            )

            if match:
                result["contract_number"] = self._clean(
                    match.group(1)
                )
                break

        # DESIGNER EXTRACTION
        # Project organization
        for line in lines:
            match = re.search(
                r"\u043f\u0440\u043e\u0435\u043a\u0442\u043d\u0430\u044f\s+"
                r"\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f\s*:\s*(.+)",
                line,
                re.IGNORECASE,
            )

            if not match:
                continue

            value = self._clean(match.group(1))

            if not value:
                continue

            ip_match = re.match(
                r"^(\u0418\u041f\s+"
                r"[\u0410-\u042f\u0401][\u0410-\u044f\u0401\u0451-]+"
                r"(?:\s+[\u0410-\u042f\u0401]\.[\u0410-\u042f\u0401]\.)?)",
                value,
            )

            if ip_match:
                result["designer"] = self._clean(ip_match.group(1))
                break

            org_match = re.match(
                r"^((?:\u041e\u041e\u041e|\u0410\u041e|\u041f\u0410\u041e|"
                r"\u041e\u0410\u041e|\u0417\u0410\u041e|\u0413\u0411\u0423|"
                r"\u0413\u0423\u041f|\u0424\u0413\u0423\u041f)\s+"
                r"(?:\"[^\"]+\"|[^;|]{2,80}))",
                value,
            )

            if org_match:
                result["designer"] = self._clean(org_match.group(1))
                break

        # ---------------------------------------------------------
        # CHIEF ENGINEER EXTRACTION
        for line in lines:
            if not re.search(
                r"\u0433\u043b\u0430\u0432\u043d\w*\s+"
                r"\u0438\u043d\u0436\u0435\u043d\u0435\u0440\s+"
                r"\u043f\u0440\u043e\u0435\u043a\u0442\u0430",
                line,
                re.IGNORECASE,
            ):
                continue

            match = re.search(
                r"([\u0410-\u042f\u0401]"
                r"[\u0410-\u044f\u0401\u0451-]+\s+"
                r"[\u0410-\u042f\u0401]\."
                r"[\u0410-\u042f\u0401]\.)",
                line,
            )

            if match:
                result["chief_engineer"] = self._clean(
                    match.group(1)
                )
                break

        # ---------------------------------------------------------
        # Адрес объекта
        # ---------------------------------------------------------

        for index, line in enumerate(lines):
            if not re.search(
                r"местоположение\s*\(адрес\)\s*объекта",
                line,
                re.IGNORECASE,
            ):
                continue

            value = self._value_after_label(
                line,
                r"местоположение\s*\(адрес\)\s*объекта",
            )

            if value and len(value) > 15:
                result["address"] = value
                break

            # В реальных штампах адрес может располагаться перед названием поля.
            value = self._previous_text(lines, index, count=2)

            if value and len(value) > 15:
                result["address"] = value
                break

        # Резервный вариант — строка "Адрес работ".
        if not result["address"]:
            for line in lines:
                match = re.search(
                    r"адрес\s+работ\s*:\s*(.+)",
                    line,
                    re.IGNORECASE,
                )

                if match:
                    result["address"] = self._clean(match.group(1))
                    break

        return result


project_metadata_analyzer = ProjectMetadataAnalyzer()
