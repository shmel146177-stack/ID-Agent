from openpyxl import load_workbook

import app.generators.document_registry_excel as excel_module
from app.generators.document_registry_excel import DocumentRegistryExcel


def test_document_registry_excel_creates_real_xlsx(monkeypatch, tmp_path):

    generator = DocumentRegistryExcel()

    registry = {
        "documents": [
            {
                "number": 1,
                "filename": "project.pdf",
                "classification": "Чертеж",
                "status": "Обработан",
                "extension": ".pdf",
                "drawing_number": "TEST-001",
                "date": "12.08.2026",
                "manufacturer": "ООО Тест",
                "equipment": "Тестовое оборудование",
            }
        ]
    }

    completeness = {
        "status": "Полный комплект",
        "profile": "project",
        "profile_name": "Проектная документация",
        "check_method": "Тестовая проверка",
        "required_count": 1,
        "found_count": 1,
        "missing_count": 0,
        "completeness_percent": 100.0,
        "documents": [
            {
                "sheet_number": 1,
                "title": "Общие данные",
                "status": "Есть",
                "matched_page": 1,
                "matched_filename": "project.pdf",
                "matched_page_type": "Общие данные",
                "score": 120,
                "confidence": "Высокая",
            }
        ],
        "missing_sheets": [],
    }

    monkeypatch.setattr(
        excel_module.document_registry,
        "build",
        lambda project_name: registry,
    )

    monkeypatch.setattr(
        excel_module.document_completeness,
        "check",
        lambda project_name: completeness,
    )

    output_path = tmp_path / "document_registry.xlsx"

    monkeypatch.setattr(
        generator,
        "_output_path",
        lambda project_name: output_path,
    )

    result = generator.create("TEST_PROJECT")

    assert result == str(output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    workbook = load_workbook(output_path)

    assert len(workbook.worksheets) == 2

    registry_sheet = workbook.worksheets[0]
    completeness_sheet = workbook.worksheets[1]

    assert "TEST_PROJECT" in str(registry_sheet["A2"].value)
    assert registry_sheet["B5"].value == "project.pdf"
    assert registry_sheet["C5"].value == "Чертеж"
    assert registry_sheet["F5"].value == "TEST-001"

    assert "TEST_PROJECT" in str(completeness_sheet["A2"].value)

    assert completeness_sheet["B6"].value == 1
    assert completeness_sheet["B7"].value == 1
    assert completeness_sheet["B8"].value == 0
    assert completeness_sheet["B9"].value == "100.0%"

    workbook.close()
