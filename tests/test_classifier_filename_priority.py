from app.analyzer.document_classifier import DocumentClassifier


def test_certificate_filename_beats_generic_scheme_text():
    classifier = DocumentClassifier()
    result = classifier.classify(
        "Сертификат.pdf",
        "Электрическая схема подключения оборудования",
    )
    assert result == "Сертификат"


def test_passport_filename_beats_generic_scheme_text():
    classifier = DocumentClassifier()
    result = classifier.classify(
        "паспорт.pdf",
        "Принципиальная схема изделия",
    )
    assert result == "Паспорт оборудования"
