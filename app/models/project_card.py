from dataclasses import dataclass


@dataclass
class ProjectCard:
    project_name: str = ""
    object_name: str = ""
    address: str = ""
    customer: str = ""
    contractor: str = ""
    designer: str = ""
    contract_number: str = ""
    start_date: str = ""
    finish_date: str = ""
    chief_engineer: str = ""