from dataclasses import dataclass


@dataclass
class ProjectCard:
    project_name: str = ""
    project_mode: str = "production"
    project_note: str = ""
    object_name: str = ""
    address: str = ""
    customer: str = ""
    contractor: str = ""
    designer: str = ""
    contract_number: str = ""
    start_date: str = ""
    finish_date: str = ""
    chief_engineer: str = ""
