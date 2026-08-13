from app.models.document_model import DocumentModel


def test_document_model_defaults_and_independent_collections():

    first = DocumentModel(
        filename="first.pdf",
        extension=".pdf",
    )

    second = DocumentModel(
        filename="second.pdf",
        extension=".pdf",
    )

    assert first.filename == "first.pdf"
    assert first.extension == ".pdf"
    assert first.document_type == "Unknown"
    assert first.pages == 0
    assert first.text == ""

    assert first.metadata == {}
    assert first.qr_codes == []
    assert first.barcodes == []
    assert first.stamps == []
    assert first.signatures == []
    assert first.images == []

    first.metadata["drawing"] = "TEST-001"
    first.images.append("page_1.png")
    first.stamps.append("stamp_1")

    assert second.metadata == {}
    assert second.images == []
    assert second.stamps == []

    assert first.metadata is not second.metadata
    assert first.images is not second.images
    assert first.stamps is not second.stamps
