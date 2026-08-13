import json
import os

from app.parsers.pdf_parser import pdf_parser
from app.services.document_analyzer import document_analyzer
from app.analyzer.document_classifier import document_classifier
from app.services.ocr_service import ocr_service


class DocumentScanner:

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
    }

    def analyze_pdf(
        self,
        file_path: str
    ) -> dict:

        filename = os.path.basename(
            file_path
        )

        # -------------------------------------------------
        # 1. СНАЧАЛА ПРОБУЕМ ОБЫЧНОЕ ИЗВЛЕЧЕНИЕ ТЕКСТА
        # -------------------------------------------------

        text = pdf_parser.extract_text(
            file_path
        )

        if text is None:
            text = ""

        text = text.strip()

        ocr_used = False
        ocr_info = None

        # -------------------------------------------------
        # 2. ЕСЛИ ТЕКСТА НЕТ — ВКЛЮЧАЕМ OCR
        # -------------------------------------------------

        if len(text) == 0:

            try:

                ocr_result = (
                    ocr_service.recognize_pdf(
                        file_path
                    )
                )

                text = (
                    ocr_result.get(
                        "text",
                        ""
                    )
                    or ""
                ).strip()

                ocr_used = True

                ocr_info = {
                    "pages_count": (
                        ocr_result.get(
                            "pages_count",
                            0
                        )
                    ),
                    "text_length": len(text),
                    "language": (
                        ocr_result.get(
                            "language",
                            "rus+eng"
                        )
                    )
                }

            except Exception as error:

                ocr_used = True

                ocr_info = {
                    "error": str(error)
                }

        # -------------------------------------------------
        # 3. АНАЛИЗ ТЕКСТА
        # -------------------------------------------------

        analysis = (
            document_analyzer.analyze_text(
                text
            )
        )

        # -------------------------------------------------
        # 4. КЛАССИФИКАЦИЯ
        # -------------------------------------------------

        classification = (
            document_classifier.classify(
                filename,
                text
            )
        )

        # Тип документа синхронизируем
        # с результатом классификатора
        if isinstance(
            analysis,
            dict
        ):
            analysis["document_type"] = (
                classification
            )

        # Для проектных чертежей не сохраняем случайные
        # характеристики оборудования из разных листов PDF.
        if (
            classification == "Чертеж"
            and isinstance(analysis, dict)
        ):
            for field in (
                "manufacturer",
                "equipment",
                "power",
                "voltage",
                "current",
                "ip",
                "frequency",
                "weight",
                "serial_number",
            ):
                analysis[field] = None


        return {
            "filename": filename,
            "path": file_path,
            "extension": ".pdf",
            "status": "Обработан",
            "classification": classification,
            "analysis": analysis,
            "text_length": len(text),
            "ocr_used": ocr_used,
            "ocr": ocr_info
        }

    def analyze_project(
        self,
        project_name: str
    ) -> dict:

        project_path = os.path.join(
            "projects",
            project_name
        )

        input_path = os.path.join(
            project_path,
            "input"
        )

        analysis_path = os.path.join(
            project_path,
            "analysis"
        )

        if not os.path.exists(
            project_path
        ):
            raise FileNotFoundError(
                f"Проект не найден: {project_name}"
            )

        if not os.path.exists(
            input_path
        ):
            raise FileNotFoundError(
                f"Папка input не найдена: {input_path}"
            )

        os.makedirs(
            analysis_path,
            exist_ok=True
        )

        documents = []

        files = sorted(
            os.listdir(
                input_path
            )
        )

        for filename in files:

            file_path = os.path.join(
                input_path,
                filename
            )

            if not os.path.isfile(
                file_path
            ):
                continue

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in (
                self.SUPPORTED_EXTENSIONS
            ):
                continue

            # ---------------------------------------------
            # PDF
            # ---------------------------------------------

            if extension == ".pdf":

                try:

                    result = self.analyze_pdf(
                        file_path
                    )

                except Exception as error:

                    result = {
                        "filename": filename,
                        "path": file_path,
                        "extension": extension,
                        "status": "Ошибка",
                        "classification": (
                            "Не определён"
                        ),
                        "analysis": {},
                        "text_length": 0,
                        "ocr_used": False,
                        "error": str(error)
                    }

            # ---------------------------------------------
            # ОСТАЛЬНЫЕ ФОРМАТЫ
            # ---------------------------------------------

            else:

                result = {
                    "filename": filename,
                    "path": file_path,
                    "extension": extension,
                    "status": (
                        "Формат определён, "
                        "анализ пока не реализован"
                    ),
                    "classification": (
                        "Не определён"
                    ),
                    "analysis": {},
                    "text_length": 0,
                    "ocr_used": False
                }

            documents.append(
                result
            )

            # ---------------------------------------------
            # JSON ДЛЯ КАЖДОГО ДОКУМЕНТА
            # ---------------------------------------------

            json_name = (
                os.path.splitext(
                    filename
                )[0]
                + ".json"
            )

            json_path = os.path.join(
                analysis_path,
                json_name
            )

            result["json_path"] = (
                json_path
            )

            with open(
                json_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    result,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

        # -------------------------------------------------
        # ОБЩИЙ РЕЗУЛЬТАТ ПРОЕКТА
        # -------------------------------------------------

        processed_count = len(
            [
                document
                for document in documents
                if document.get(
                    "status"
                ) == "Обработан"
            ]
        )

        result = {
            "project": project_name,
            "documents_count": len(
                documents
            ),
            "processed_count": (
                processed_count
            ),
            "documents": documents
        }

        project_analysis_path = os.path.join(
            analysis_path,
            "project_analysis.json"
        )

        with open(
            project_analysis_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4
            )

        return result


document_scanner = DocumentScanner()
