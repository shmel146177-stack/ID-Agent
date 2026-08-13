from app.models.project import Project


def test_project_model_defaults_and_values():

    empty_project = Project()

    assert empty_project.object_name == ""
    assert empty_project.customer == ""
    assert empty_project.contractor == ""
    assert empty_project.equipment == ""
    assert empty_project.manufacturer == ""
    assert empty_project.drawing_number == ""
    assert empty_project.document_type == ""
    assert empty_project.date == ""
    assert empty_project.voltage == ""
    assert empty_project.current == ""
    assert empty_project.power == ""
    assert empty_project.ip == ""
    assert empty_project.serial_number == ""

    project = Project(
        object_name="ТП-101",
        customer="ООО Заказчик",
        contractor="ООО Подрядчик",
        equipment="Шкаф управления",
        manufacturer="ООО Производитель",
        drawing_number="TEST-001",
        document_type="Чертеж",
        date="12.08.2026",
        voltage="400 В",
        current="16 А",
        power="7,5 кВт",
        ip="IP66",
        serial_number="SN-001",
    )

    assert project.object_name == "ТП-101"
    assert project.customer == "ООО Заказчик"
    assert project.contractor == "ООО Подрядчик"
    assert project.equipment == "Шкаф управления"
    assert project.manufacturer == "ООО Производитель"
    assert project.drawing_number == "TEST-001"
    assert project.document_type == "Чертеж"
    assert project.date == "12.08.2026"
    assert project.voltage == "400 В"
    assert project.current == "16 А"
    assert project.power == "7,5 кВт"
    assert project.ip == "IP66"
    assert project.serial_number == "SN-001"
