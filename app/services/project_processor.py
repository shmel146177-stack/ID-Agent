from app.generators.document_registry_excel import document_registry_excel
from app.generators.hidden_works_act_generator import hidden_works_act_generator
from app.generators.hidden_works_journal_generator import (
    hidden_works_journal_generator,
)
from app.generators.project_report_generator import project_report_generator
from app.services.document_completeness import document_completeness
from app.services.document_registry import document_registry
from app.services.executive_document_router import executive_document_router
from app.services.document_scanner import document_scanner
from app.services.drawing_register_service import drawing_register_service
from app.services.page_analysis_service import page_analysis_service
from app.services.project_metadata_service import project_metadata_service
from app.services.project_section_exporter import project_section_exporter


class ProjectProcessor:

    def process(
        self,
        project_name: str,
    ) -> dict:

        result = {
            "project": project_name,
            "status": "Начато",
        }

        # ---------------------------------------------------------
        # 1. СКАНИРОВАНИЕ И АНАЛИЗ ДОКУМЕНТОВ
        # ---------------------------------------------------------

        scan_result = document_scanner.analyze_project(project_name)

        result["scan"] = scan_result

        # ---------------------------------------------------------
        # 2. ПОСТРАНИЧНЫЙ АНАЛИЗ + OCR
        # ---------------------------------------------------------

        page_analysis_result = page_analysis_service.analyze_project(project_name)

        result["page_analysis"] = page_analysis_result

        # ---------------------------------------------------------
        # 3. ЭКСПОРТ СТРАНИЦ ПО РАЗДЕЛАМ
        #
        # 01 - Исходные документы
        # 02 - Рабочая документация
        # ---------------------------------------------------------

        section_export_result = project_section_exporter.export_project(project_name)

        result["section_export"] = section_export_result

        # ---------------------------------------------------------
        # 4. ВЕДОМОСТЬ РАБОЧИХ ЧЕРТЕЖЕЙ
        # ---------------------------------------------------------

        drawing_register_result = drawing_register_service.analyze_project(project_name)

        result["drawing_register"] = drawing_register_result

        # ---------------------------------------------------------
        # 5. ИЗВЛЕЧЕНИЕ РЕКВИЗИТОВ ПРОЕКТА
        # ---------------------------------------------------------

        metadata_result = project_metadata_service.update_from_project(project_name)

        result["metadata"] = metadata_result

        # ---------------------------------------------------------
        # 6. РЕЕСТР ДОКУМЕНТОВ
        # ---------------------------------------------------------

        registry_result = document_registry.build(project_name)

        result["registry"] = registry_result

        # ---------------------------------------------------------
        # 7. ПРОВЕРКА КОМПЛЕКТНОСТИ
        # ---------------------------------------------------------

        completeness_result = document_completeness.check(project_name)

        result["completeness"] = completeness_result


        # ---------------------------------------------------------
        # ROUTE DOCUMENTS TO EXECUTIVE DOCUMENTATION SECTIONS
        # ---------------------------------------------------------

        routing_result = executive_document_router.route(project_name)

        result["document_routing"] = routing_result

        # ---------------------------------------------------------
        # 8. АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ЧЕРНОВИКОВ АОСР
        # ---------------------------------------------------------

        hidden_works_acts_result = hidden_works_act_generator.create_all(project_name)

        result["hidden_works_acts"] = hidden_works_acts_result

        # ---------------------------------------------------------
        # 9. ЖУРНАЛ СКРЫТЫХ РАБОТ
        # ---------------------------------------------------------

        hidden_works_journal_path = hidden_works_journal_generator.create(project_name)

        result["hidden_works_journal"] = hidden_works_journal_path

        # ---------------------------------------------------------
        # 10. EXCEL-РЕЕСТР
        # ---------------------------------------------------------

        excel_path = document_registry_excel.create(project_name)

        result["excel"] = excel_path

        # ---------------------------------------------------------
        # 11. ИТОГОВЫЙ DOCX-ОТЧЁТ
        # ---------------------------------------------------------

        report_path = project_report_generator.create(project_name)

        result["report"] = report_path

        # ---------------------------------------------------------
        # ГОТОВО
        # ---------------------------------------------------------

        result["status"] = "Готово"

        return result


project_processor = ProjectProcessor()
