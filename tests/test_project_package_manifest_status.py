from app.services.project_package import ProjectPackage


READY = "\u0413\u043e\u0442\u043e\u0432\u043e"

INCOMPLETE = (
    "\u041d\u0435\u043f\u043e\u043b\u043d\u044b\u0439 "
    "\u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"
)

DRAFT = (
    "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a. "
    "\u0422\u0440\u0435\u0431\u0443\u0435\u0442 "
    "\u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f"
)

WAITING_DOCUMENTS = (
    "\u041e\u0436\u0438\u0434\u0430\u0435\u0442 "
    "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432"
)

NOT_FORMED = (
    "\u041d\u0435 "
    "\u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d"
)


def resolve_status(
    *,
    missing_count=0,
    acts_detected=0,
    acts_confirmation=False,
    journal_status=READY,
    supporting_confirmation=False,
    supporting_sections=None,
):

    package = ProjectPackage()

    return package._resolve_manifest_status(
        {
            "status": READY,
            "completeness": {
                "missing_count": missing_count,
            },
        },
        {
            "acts_detected": acts_detected,
            "requires_field_confirmation": acts_confirmation,
        },
        {
            "status": journal_status,
        },
        {
            "requires_field_confirmation": (
                supporting_confirmation
            ),
            "sections": supporting_sections or [],
        },
    )


def test_manifest_status_is_incomplete_when_sheet_is_missing():

    status = resolve_status(
        missing_count=1,
    )

    assert status == INCOMPLETE


def test_manifest_status_is_incomplete_when_documents_are_waiting():

    status = resolve_status(
        supporting_sections=[
            {
                "status": WAITING_DOCUMENTS,
            }
        ],
    )

    assert status == INCOMPLETE


def test_manifest_status_is_incomplete_when_journal_is_missing():

    status = resolve_status(
        acts_detected=1,
        journal_status=NOT_FORMED,
    )

    assert status == INCOMPLETE


def test_manifest_status_is_draft_when_acts_require_confirmation():

    status = resolve_status(
        acts_confirmation=True,
    )

    assert status == DRAFT


def test_manifest_status_is_draft_when_documents_require_confirmation():

    status = resolve_status(
        supporting_confirmation=True,
    )

    assert status == DRAFT


def test_manifest_status_is_draft_when_journal_is_draft():

    status = resolve_status(
        journal_status=DRAFT,
    )

    assert status == DRAFT


def test_manifest_status_is_ready_when_all_checks_are_clear():

    status = resolve_status()

    assert status == READY
