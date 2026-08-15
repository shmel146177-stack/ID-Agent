from app.analyzer.document_classifier import DocumentClassifier


def test_classifier_detects_executive_scheme():
    classifier = DocumentClassifier()

    result = classifier.classify(
        "document.pdf",
        "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0437\u0430\u0437\u0435\u043c\u043b\u044f\u044e\u0449\u0435\u0433\u043e \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430",
    )

    assert result == "\u0418\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430"


def test_classifier_keeps_electrical_scheme_as_regular_scheme():
    classifier = DocumentClassifier()

    result = classifier.classify(
        "document.pdf",
        "\u042d\u043b\u0435\u043a\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043f\u0440\u0438\u043d\u0446\u0438\u043f\u0438\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430",
    )

    assert result == "\u0421\u0445\u0435\u043c\u0430"
