from pathlib import Path

import fitz
import pytest

import app.services.drawing_attachment_audit as audit_module
from app.services.drawing_attachment_audit import DrawingAttachmentAudit


def _font_path() -> Path:
    for candidate in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ):
        if candidate.is_file():
            return candidate
    pytest.skip("No Cyrillic font available for PDF fixture")


def _add_text(page, font_path, position, text):
    page.insert_font(fontname="unicode", fontfile=str(font_path))
    page.insert_text(position, text, fontname="unicode", fontsize=12)


@pytest.mark.parametrize(
    ("declared_sheets", "second_designation", "expected_warning_codes"),
    [
        (
            1,
            "98766/26-КЖ.СП2",
            {"sheet_count_mismatch", "designation_mismatch_candidate"},
        ),
        (2, "98765/26-КЖ.СП2", set()),
    ],
)
def test_attachment_audit_uses_register_and_stamps_from_another_project(
    monkeypatch,
    tmp_path,
    declared_sheets,
    second_designation,
    expected_warning_codes,
):
    font_path = _font_path()
    project_path = tmp_path / "project"
    input_path = project_path / "input"
    input_path.mkdir(parents=True)
    source_pdf = input_path / "source.pdf"
    with fitz.open() as pdf:
        register = pdf.new_page(width=1191, height=842)
        _add_text(register, font_path, (700, 100), "Прилагаемые документы")
        _add_text(register, font_path, (700, 130), "98765/26-КЖ.СП1")
        _add_text(register, font_path, (700, 160), "98765/26-КЖ.СП2")
        first = pdf.new_page(width=1191, height=842)
        _add_text(first, font_path, (800, 760), "98765/26-КЖ.СП1")
        _add_text(first, font_path, (1125, 740), "Листов")
        _add_text(first, font_path, (1140, 766), str(declared_sheets))
        continuation = pdf.new_page(width=1191, height=842)
        _add_text(continuation, font_path, (800, 760), "98765/26-КЖ.СП1")
        second = pdf.new_page(width=1191, height=842)
        _add_text(second, font_path, (800, 760), second_designation)
        _add_text(second, font_path, (1125, 740), "Листов")
        _add_text(second, font_path, (1140, 766), "1")
        pdf.save(source_pdf)

    monkeypatch.setattr(audit_module, "safe_project_path", lambda name: project_path)
    result = DrawingAttachmentAudit().analyze(
        "OTHER_PROJECT", {"registers": [{"filename": "source.pdf", "page": 1}]}
    )

    assert len(result["documents"]) == 2
    assert {warning["code"] for warning in result["warnings"]} == expected_warning_codes
    assert result["status"] == ("warnings" if expected_warning_codes else "no_warnings")
    assert result["unchecked"] == []
    if expected_warning_codes:
        assert result["warnings"][0]["pages"] == [2, 3]
        assert result["warnings"][0]["declared_sheets"] == 1
        assert result["warnings"][1]["expected_designation"] == "98765/26-КЖ.СП2"
        assert result["warnings"][1]["observed_designation"] == second_designation


def test_attachment_audit_does_not_guess_when_register_is_unavailable(
    monkeypatch, tmp_path
):
    project_path = tmp_path / "project"
    input_path = project_path / "input"
    input_path.mkdir(parents=True)
    with fitz.open() as pdf:
        pdf.new_page(width=1191, height=842)
        pdf.save(input_path / "source.pdf")

    monkeypatch.setattr(audit_module, "safe_project_path", lambda name: project_path)
    result = DrawingAttachmentAudit().analyze(
        "OTHER_PROJECT", {"registers": [{"filename": "source.pdf", "page": 1}]}
    )

    assert result["status"] == "not_checked"
    assert result["warnings"] == []
    assert result["unchecked"][0]["reason"] == "attached_register_unreadable_or_absent"
