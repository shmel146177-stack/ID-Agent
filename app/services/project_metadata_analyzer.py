import re


class ProjectMetadataAnalyzer:
    """Extract construction project metadata from PDF text."""

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
        """Collect content before a stamp label, omitting neighboring labels."""
        values = []
        for pos in range(index - 1, max(-1, index - count - 1), -1):
            line = self._clean(lines[pos])
            if not line:
                continue
            if line.lower() in {
                "изм.",
                "лист",
                "листов",
                "подпись",
                "дата",
                "разработал",
                "проверил",
                "стадия",
                "заказчик",
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
        match = re.search(
            rf"{label_pattern}\s*:?\s*(.+)$",
            line,
            re.IGNORECASE,
        )
        if not match:
            return None
        return self._clean(match.group(1))

    def _first_match(self, lines: list[str], pattern: str) -> str | None:
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return self._clean(match.group(1))
        return None

    def _title_page_metadata(self, lines: list[str]) -> dict[str, str | None]:
        metadata = {
            "object_name": None,
            "address": None,
            "customer": self._first_match(
                lines,
                r"^\s*заказчик\s*[—–-]\s*(.+)$",
            ),
            "designer": None,
        }
        title_index = next(
            (
                index
                for index, line in enumerate(lines)
                if re.search(r"рабочая\s+документация", line, re.IGNORECASE)
            ),
            None,
        )
        if title_index is None:
            return metadata

        object_lines = []
        for line in lines[max(0, title_index - 12) : title_index]:
            clean_line = self._clean(line)
            if not clean_line:
                continue
            if re.search(r"^строительство\b", clean_line, re.IGNORECASE):
                object_lines = [clean_line]
            elif object_lines:
                object_lines.append(clean_line)

        if object_lines:
            metadata["object_name"] = self._clean(" ".join(object_lines))
            address_match = re.search(
                r"(Московская\s+область\s*,.+?)(?:\s*\([^)]*МВА[^)]*\))?$",
                metadata["object_name"],
                re.IGNORECASE,
            )
            if address_match:
                metadata["address"] = self._clean(address_match.group(1))

        header = " ".join(
            self._clean(line) or "" for line in lines[: min(title_index, 12)]
        )
        designer_match = re.search(
            r"Общество\s+с\s+ограниченной\s+ответственностью\s+" r'[«"]([^»"]+)[»"]',
            header,
            re.IGNORECASE,
        )
        if designer_match:
            metadata["designer"] = f"ООО «{designer_match.group(1)}»"
        return metadata

    def _stamp_object_name(self, lines: list[str]) -> str | None:
        for index, line in enumerate(lines):
            if not re.search(r"наименование\s+объекта", line, re.IGNORECASE):
                continue

            value = self._value_after_label(line, r"наименование\s+объекта")
            if value and len(value) > 15:
                for offset in range(1, 4):
                    if index + offset >= len(lines):
                        break
                    next_line = self._clean(lines[index + offset])
                    if not next_line:
                        continue
                    if sum(char.isalpha() for char in next_line) < 8:
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
                return value

            value = self._previous_text(lines, index, count=2)
            if value and len(value) > 15:
                return value
        return None

    def _stamp_customer(self, lines: list[str]) -> str | None:
        for index, line in enumerate(lines):
            if not re.search(r"^\s*заказчик\s*:?\s*$", line, re.IGNORECASE):
                continue
            value = self._previous_text(lines, index, count=1)
            if value and any(
                marker in value for marker in ("ООО", "АО ", "ПАО ", "ИП ", "ГБУ ")
            ):
                return value
        return self._first_match(lines, r"организация\s+заказчика\s*:\s*(.+)")

    def _contractor(self, lines: list[str]) -> str | None:
        return self._first_match(
            lines,
            r"(?:генеральн\w*\s+подрядчик|"
            r"подрядн\w*\s+организаци\w*|"
            r"организаци\w*\s+подрядчика|"
            r"подрядчик)\s*:\s*(.+)",
        )

    def _contract_number(self, lines: list[str]) -> str | None:
        return self._first_match(
            lines,
            r"(?:договор(?:\s+подряда)?|контракт)"
            r"\s*(?:№|N(?:o)?\.?)\s*"
            r"([0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё./_-]*)",
        )

    def _stamp_designer(self, lines: list[str]) -> str | None:
        for line in lines:
            match = re.search(
                r"проектная\s+организация\s*:\s*(.+)",
                line,
                re.IGNORECASE,
            )
            if not match:
                continue
            value = self._clean(match.group(1))
            if not value:
                continue

            ip_match = re.match(
                r"^(ИП\s+[А-ЯЁ][А-яЁё-]+" r"(?:\s+[А-ЯЁ]\.[А-ЯЁ]\.)?)",
                value,
            )
            if ip_match:
                return self._clean(ip_match.group(1))

            org_match = re.match(
                r"^((?:ООО|АО|ПАО|ОАО|ЗАО|ГБУ|ГУП|ФГУП)\s+"
                r"(?:\"[^\"]+\"|[^;|]{2,80}))",
                value,
            )
            if org_match:
                return self._clean(org_match.group(1))
        return None

    def _chief_engineer(self, lines: list[str]) -> str | None:
        for line in lines:
            if not re.search(
                r"главн\w*\s+инженер\s+проекта",
                line,
                re.IGNORECASE,
            ):
                continue
            match = re.search(
                r"([А-ЯЁ][А-яЁё-]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)",
                line,
            )
            if match:
                return self._clean(match.group(1))
        return None

    def _stamp_address(self, lines: list[str]) -> str | None:
        label_pattern = r"местоположение\s*\(адрес\)\s*объекта"
        for index, line in enumerate(lines):
            if not re.search(label_pattern, line, re.IGNORECASE):
                continue
            value = self._value_after_label(line, label_pattern)
            if value and len(value) > 15:
                return value
            value = self._previous_text(lines, index, count=2)
            if value and len(value) > 15:
                return value
        return self._first_match(lines, r"адрес\s+работ\s*:\s*(.+)")

    def analyze_text(self, text: str) -> dict:
        lines = text.splitlines()
        title = self._title_page_metadata(lines)
        object_name = title["object_name"] or self._stamp_object_name(lines)
        customer = title["customer"] or self._stamp_customer(lines)
        contractor = self._contractor(lines)
        contract_number = self._contract_number(lines)
        designer = title["designer"] or self._stamp_designer(lines)
        chief_engineer = self._chief_engineer(lines)
        address = title["address"] or self._stamp_address(lines)

        return {
            "object_name": object_name,
            "address": address,
            "customer": customer,
            "contractor": contractor,
            "designer": designer,
            "chief_engineer": chief_engineer,
            "contract_number": contract_number,
        }


project_metadata_analyzer = ProjectMetadataAnalyzer()
