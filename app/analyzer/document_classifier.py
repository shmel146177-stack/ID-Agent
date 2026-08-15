import os
import re


class DocumentClassifier:

    STRONG_TEXT_MARKERS = {
        "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430": [
            "\u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
        ],
        "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f": [
            "\u043f\u0430\u0441\u043f\u043e\u0440\u0442 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f",
            "\u043f\u0430\u0441\u043f\u043e\u0440\u0442 \u0438\u0437\u0434\u0435\u043b\u0438\u044f",
            "\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u043f\u0430\u0441\u043f\u043e\u0440\u0442",
        ],
        "\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442": [
            "\u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u044f",
        ],
        "\u0414\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f": [
            "\u0434\u0435\u043a\u043b\u0430\u0440\u0430\u0446\u0438\u044f \u043e \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u0438",
        ],
        "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b": [
            "\u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u0439",
            "\u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u0439",
            "\u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438",
        ],
    }

    def __init__(self):

        self.filename_rules = {
            "Паспорт оборудования": [
                "паспорт",
                "passport",
            ],
            "Сертификат": [
                "сертификат",
                "certificate",
            ],
            "Схема": [
                "схема",
                "scheme",
                "diagram",
            ],
            "Чертеж": [
                "чертеж",
                "чертёж",
                "drawing",
            ],
            "Протокол": [
                "протокол",
                "protocol",
            ],
            "Руководство": [
                "руководство",
                "инструкция",
                "manual",
            ],
            "Декларация": [
                "декларация",
                "declaration",
            ],
            "АОСР": [
                "аоср",
                "скрытых работ",
            ],
            "Счет-фактура": [
                "счет-фактура",
                "счет фактура",
                "счёт-фактура",
                "счёт фактура",
                "invoice",
            ],
        }

        self.text_rules = {

            "Паспорт оборудования": {
                "паспорт": 8,
                "паспорт изделия": 10,
                "паспорт оборудования": 10,
                "технический паспорт": 10,
                "заводской номер": 3,
                "серийный номер": 3,
                "изготовитель": 2,
                "технические характеристики": 4,
            },

            "Сертификат": {
                "сертификат соответствия": 12,
                "сертификат": 8,
                "соответствует требованиям": 4,
                "орган по сертификации": 6,
                "сертификации": 3,
                "заявитель": 2,
            },

            "Схема": {
                "принципиальная схема": 12,
                "электрическая схема": 12,
                "схема электрическая": 12,
                "схема подключения": 10,
                "схема соединений": 10,
                "схема": 4,
            },

            "Чертеж": {
                "чертеж": 8,
                "чертёж": 8,
                "номер чертежа": 10,
                "масштаб": 3,
                "формат": 2,
                "разработал": 2,
                "проверил": 2,
            },

            "Протокол": {
                "протокол испытаний": 12,
                "протокол измерений": 12,
                "протокол проверки": 10,
                "протокол": 7,
                "результаты испытаний": 5,
                "результаты измерений": 5,
                "испытание": 2,
                "измерение": 2,
            },

            "Руководство": {
                "руководство по эксплуатации": 12,
                "инструкция по эксплуатации": 12,
                "руководство": 7,
                "инструкция": 6,
                "меры безопасности": 4,
                "техническое обслуживание": 4,
                "эксплуатация": 3,
            },

            "Декларация": {
                "декларация о соответствии": 12,
                "декларация": 8,
                "декларирование соответствия": 6,
                "соответствует требованиям": 3,
            },

            "АОСР": {
                "акт освидетельствования скрытых работ": 15,
                "освидетельствования скрытых работ": 12,
                "скрытых работ": 8,
                "к освидетельствованию предъявлены": 8,
                "последующие работы": 3,
            },

            "Счет-фактура": {
                "счет-фактура": 20,
                "счет фактура": 20,
                "счёт-фактура": 20,
                "счёт фактура": 20,
                "продавец": 5,
                "покупатель": 5,
                "инн/кпп продавца": 8,
                "инн/кпп покупателя": 8,
                "грузоотправитель": 4,
                "грузополучатель": 4,
                "всего к оплате": 6,
                "наименование товара": 4,
                "единица измерения": 3,
                "налоговая ставка": 3,
            },
        }

    def _normalize(
        self,
        value: str
    ) -> str:

        if not value:
            return ""

        value = value.lower()

        value = value.replace(
            "ё",
            "е"
        )

        # OCR иногда ставит разные тире
        value = value.replace(
            "–",
            "-"
        )

        value = value.replace(
            "—",
            "-"
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    def _classify_by_filename(
        self,
        filename: str
    ):

        normalized_filename = (
            self._normalize(
                os.path.basename(
                    filename
                )
            )
        )

        for document_type, keywords in (
            self.filename_rules.items()
        ):

            for keyword in keywords:

                normalized_keyword = (
                    self._normalize(
                        keyword
                    )
                )

                if (
                    normalized_keyword
                    in normalized_filename
                ):
                    return document_type

        return None

    def _classify_by_strong_markers(
        self,
        text: str,
    ):

        normalized_text = self._normalize(text)

        if not normalized_text:
            return None

        for document_type, phrases in self.STRONG_TEXT_MARKERS.items():

            for phrase in phrases:

                normalized_phrase = self._normalize(phrase)

                if normalized_phrase in normalized_text:
                    return document_type

        return None

    def _classify_by_text(
        self,
        text: str
    ):

        normalized_text = (
            self._normalize(
                text
            )
        )

        if not normalized_text:
            return None

        scores = {}

        for document_type, rules in (
            self.text_rules.items()
        ):

            score = 0

            for phrase, weight in (
                rules.items()
            ):

                normalized_phrase = (
                    self._normalize(
                        phrase
                    )
                )

                occurrences = (
                    normalized_text.count(
                        normalized_phrase
                    )
                )

                if occurrences > 0:

                    occurrences = min(
                        occurrences,
                        3
                    )

                    score += (
                        weight
                        * occurrences
                    )

            scores[
                document_type
            ] = score

        if not scores:
            return None

        best_type = max(
            scores,
            key=scores.get
        )

        best_score = scores[
            best_type
        ]

        if best_score < 5:
            return None

        return best_type

    def classify(
        self,
        filename,
        text: str = ""
    ):

        document = None

        # Поддержка DocumentModel
        if not isinstance(filename, (str, bytes, os.PathLike)):
            document = filename

            filename = getattr(
                document,
                "filename",
                ""
            )

            if not text:
                text = getattr(
                    document,
                    "text",
                    ""
                )

        # 1. Strong text markers have highest priority
        filename_result = self._classify_by_filename(filename)

        priority_filename_types = {
            "Паспорт оборудования",
            "Сертификат",
            "Декларация",
        }

        if filename_result in priority_filename_types:
            result = filename_result
        else:
            result = self._classify_by_strong_markers(text)

        # 2. Text / OCR scoring
        if not result:
            result = self._classify_by_text(text)

        # 3. Filename is fallback only
        if not result:
            result = self._classify_by_filename(filename)

        if not result:
            result = "Не определён"

        # Старый интерфейс: classify(DocumentModel)
        if document is not None:
            document.document_type = result
            return document

        # Новый интерфейс: classify(filename, text)
        return result
document_classifier = DocumentClassifier()
