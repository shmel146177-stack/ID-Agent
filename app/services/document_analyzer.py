import re


class DocumentAnalyzer:

    def analyze_text(self, text: str):

        result = {
            "document_type": "Не определён",
            "manufacturer": None,
            "equipment": None,
            "date": None,
            "drawing_number": None,
            "power": None,
            "voltage": None,
            "current": None,
            "ip": None,
            "frequency": None,
            "weight": None,
            "serial_number": None
        }

        text_lower = text.lower()

        # Тип документа
        if "паспорт" in text_lower:
            result["document_type"] = "Паспорт оборудования"

        elif "шкаф управления" in text_lower:
            result["document_type"] = "Документация оборудования"

        # Изготовитель
        match = re.search(
            r'ООО\s+"[^"]+"',
            text
        )

        if match:
            result["manufacturer"] = match.group().strip()

        # Дата
        match = re.search(
            r"\d{2}\.\d{2}\.\d{4}",
            text
        )

        if match:
            result["date"] = match.group()

        # Номер чертежа
        match = re.search(
            r"[А-ЯA-Z]{2,}\.\d+\.[А-ЯA-Z0-9\-]+",
            text
        )

        if match:
            result["drawing_number"] = match.group()

        # Оборудование
        match = re.search(
            r"Шкаф управления[^\n]+",
            text,
            re.IGNORECASE
        )

        if match:
            result["equipment"] = match.group().strip()

        # Мощность
        match = re.search(
            r"\d+(?:,\d+)?\s*кВт",
            text,
            re.IGNORECASE
        )

        if match:
            result["power"] = match.group().strip()

        # Номинальный ток
        match = re.search(
            r"Iном\s*=?\s*\(?([0-9]+\s*-\s*[0-9]+)\)?\s*А",
            text,
            re.IGNORECASE
        )

        if match:
            result["current"] = match.group(1).strip() + " А"

        # Напряжение
        match = re.search(
            r"\b\d+(?:,\d+)?\s*В\b",
            text,
            re.IGNORECASE
        )

        if match:
            result["voltage"] = match.group().strip()

        # Степень защиты
        match = re.search(
            r"\bIP\s*\d{2}\b",
            text,
            re.IGNORECASE
        )

        if match:
            result["ip"] = (
                match.group()
                .replace(" ", "")
                .upper()
            )

        # Частота
        match = re.search(
            r"\b\d+\s*Гц\b",
            text,
            re.IGNORECASE
        )

        if match:
            value = match.group().strip()
            value = re.sub(
                r"\s*Гц",
                " Гц",
                value,
                flags=re.IGNORECASE
            )

            result["frequency"] = value

        # Масса
        match = re.search(
            r"\b\d+(?:,\d+)?\s*кг\b",
            text,
            re.IGNORECASE
        )

        if match:
            result["weight"] = match.group().strip()

        # Серийный / заводской номер
        #
        # Ищем номер только если перед ним явно написано:
        # "Серийный номер", "Заводской номер", "Зав. №"
        #
        serial_patterns = [
            r"серийный\s+номер\s*[:№]?\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-\/\.]{2,})",
            r"заводской\s+номер\s*[:№]?\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-\/\.]{2,})",
            r"зав\.\s*№\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-\/\.]{2,})"
        ]

        for pattern in serial_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                serial_number = match.group(1).strip()

                # Защита от случайных слов вроде "дубл"
                if any(char.isdigit() for char in serial_number):
                    result["serial_number"] = serial_number

                break

        return result


document_analyzer = DocumentAnalyzer()