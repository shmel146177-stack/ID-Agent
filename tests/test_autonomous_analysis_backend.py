from app.services.autonomous_analysis_backend import (
    AutonomousAnalysisBackend,
)


class ClassifierStub:
    def __init__(self):
        self.calls = []

    def classify(self, filename, text):
        self.calls.append((filename, text))
        return "Паспорт оборудования"


class AnalyzerStub:
    def __init__(self):
        self.calls = []

    def analyze_text(self, text):
        self.calls.append(text)
        return {
            "document_type": "Документация оборудования",
            "manufacturer": 'ООО "Тест"',
            "power": "7,5 кВт",
            "serial_number": None,
        }


def test_autonomous_backend_builds_reviewable_analysis():
    classifier = ClassifierStub()
    analyzer = AnalyzerStub()
    backend = AutonomousAnalysisBackend(
        classifier=classifier,
        analyzer=analyzer,
    )

    result = backend(
        "passport.pdf",
        'Паспорт. Изготовитель ООО "Тест". Мощность 7,5 кВт.',
    )

    assert classifier.calls == [
        (
            "passport.pdf",
            'Паспорт. Изготовитель ООО "Тест". Мощность 7,5 кВт.',
        )
    ]
    assert analyzer.calls == [
        'Паспорт. Изготовитель ООО "Тест". Мощность 7,5 кВт.'
    ]
    assert result.document_type_suggestion == "Паспорт оборудования"
    assert {
        fact.field: fact.value
        for fact in result.facts
    } == {
        "manufacturer": 'ООО "Тест"',
        "power": "7,5 кВт",
    }
    assert all(
        fact.value in fact.evidence
        for fact in result.facts
    )
    assert all(fact.confidence < 1.0 for fact in result.facts)
    assert result.requires_human_review is True
    assert result.engineering_confirmation is False
    assert any(
        "автоном" in warning.lower()
        for warning in result.warnings
    )


def test_autonomous_backend_uses_existing_project_analyzers():
    backend = AutonomousAnalysisBackend()

    result = backend(
        "паспорт.pdf",
        (
            "Паспорт оборудования\n"
            'ООО "Тест"\n'
            "Шкаф управления ШУ-1, 7,5 кВт\n"
            "IP 54\n"
            "Серийный номер ABC-123"
        ),
    )

    facts = {
        fact.field: fact.value
        for fact in result.facts
    }

    assert result.document_type_suggestion == "Паспорт оборудования"
    assert facts["manufacturer"] == 'ООО "Тест"'
    assert facts["equipment"] == "Шкаф управления ШУ-1, 7,5 кВт"
    assert facts["power"] == "7,5 кВт"
    assert facts["ip"] == "IP54"
    assert facts["serial_number"] == "ABC-123"

def test_autonomous_backend_uses_source_lines_as_evidence():
    backend = AutonomousAnalysisBackend(
        classifier=ClassifierStub(),
        analyzer=AnalyzerStub(),
    )
    text = (
        "Паспорт оборудования\n"
        'Изготовитель: ООО "Тест"\n'
        "Номинальная мощность шкафа: 7,5 кВт."
    )

    result = backend(
        "passport.pdf",
        text,
    )
    evidence = {
        fact.field: fact.evidence
        for fact in result.facts
    }

    assert evidence["manufacturer"] == 'Изготовитель: ООО "Тест"'
    assert evidence["power"] == "Номинальная мощность шкафа: 7,5 кВт."

def test_autonomous_backend_limits_evidence_fragment_length():
    backend = AutonomousAnalysisBackend(
        classifier=ClassifierStub(),
        analyzer=AnalyzerStub(),
    )
    text = (
        ("А" * 300)
        + " Номинальная мощность 7,5 кВт. "
        + ("Б" * 300)
    )

    result = backend(
        "passport.pdf",
        text,
    )
    power_fact = next(
        fact
        for fact in result.facts
        if fact.field == "power"
    )

    assert power_fact.evidence is not None
    assert len(power_fact.evidence) <= 240
    assert power_fact.value in power_fact.evidence

def test_autonomous_backend_finds_evidence_with_spacing_difference():
    class IPAnalyzerStub:
        def analyze_text(self, text):
            return {
                "document_type": "Документация оборудования",
                "ip": "IP54",
            }

    backend = AutonomousAnalysisBackend(
        classifier=ClassifierStub(),
        analyzer=IPAnalyzerStub(),
    )

    result = backend(
        "passport.pdf",
        "Степень защиты корпуса: IP 54.",
    )
    ip_fact = next(
        fact
        for fact in result.facts
        if fact.field == "ip"
    )

    assert ip_fact.value == "IP54"
    assert ip_fact.evidence == "Степень защиты корпуса: IP 54."

def test_autonomous_backend_does_not_invent_missing_evidence():
    class MissingEvidenceAnalyzerStub:
        def analyze_text(self, text):
            return {
                "document_type": "Не определён",
                "serial_number": "ABC-123",
            }

    backend = AutonomousAnalysisBackend(
        classifier=ClassifierStub(),
        analyzer=MissingEvidenceAnalyzerStub(),
    )

    result = backend(
        "document.pdf",
        "Текст документа без серийного номера.",
    )
    serial_fact = next(
        fact
        for fact in result.facts
        if fact.field == "serial_number"
    )

    assert serial_fact.value == "ABC-123"
    assert serial_fact.evidence is None