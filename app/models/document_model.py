from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DocumentModel:
    filename: str
    extension: str
    document_type: str = "Unknown"

    pages: int = 0

    text: str = ""

    metadata: Dict = field(default_factory=dict)

    qr_codes: List = field(default_factory=list)

    barcodes: List = field(default_factory=list)

    stamps: List = field(default_factory=list)

    signatures: List = field(default_factory=list)

    images: List = field(default_factory=list)