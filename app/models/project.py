from dataclasses import dataclass


@dataclass
class Project:

    object_name: str = ""

    customer: str = ""

    contractor: str = ""

    equipment: str = ""

    manufacturer: str = ""

    drawing_number: str = ""

    document_type: str = ""

    date: str = ""

    voltage: str = ""

    current: str = ""

    power: str = ""

    ip: str = ""

    serial_number: str = ""