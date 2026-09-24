import json

from app.services.hidden_works_registry import HiddenWorksRegistry


def test_hidden_works_registry_detects_act(monkeypatch, tmp_path):

    registry = HiddenWorksRegistry()

    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"

    project_path.mkdir(parents=True)

    rule = registry.RULES[0]

    monkeypatch.setattr(
        registry,
        "_project_path",
        lambda project_name: project_path,
    )

    monkeypatch.setattr(
        registry,
        "_analysis_path",
        lambda project_name: analysis_path,
    )

    monkeypatch.setattr(
        registry,
        "_extract_register_entries",
        lambda project_name: [],
    )

    monkeypatch.setattr(
        registry,
        "_load_page_types",
        lambda project_name: {
            rule["page_types"][0]: 1,
        },
    )

    result = registry.analyze_project(
        "TEST_PROJECT"
    )

    assert result["project"] == "TEST_PROJECT"
    assert result["acts_count"] == 1
    assert result["requires_field_confirmation"] is True

    act = result["acts"][0]

    assert act["code"] == rule["code"]
    assert act["title"] == rule["title"]
    assert act["act_title"] == rule["act_title"]
    assert act["confirmation_required"] is True
    assert len(act["evidence"]) == 1

    output_path = analysis_path / "hidden_works_registry.json"

    assert output_path.exists()
    assert result["analysis_file"] == str(output_path)

    saved = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved["acts_count"] == 1
    assert saved["acts"][0]["code"] == rule["code"]


def test_work_volume_candidates_do_not_become_acts(monkeypatch, tmp_path):
    registry = HiddenWorksRegistry()
    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"
    analysis_path.mkdir(parents=True)

    monkeypatch.setattr(registry, "_project_path", lambda _: project_path)
    monkeypatch.setattr(registry, "_analysis_path", lambda _: analysis_path)
    monkeypatch.setattr(registry, "_extract_register_entries", lambda _: [])

    page_analysis = {
        "documents": [
            {
                "filename": "Том АС.pdf",
                "pages": [
                    {
                        "page": 37,
                        "page_type": "Ведомость объемов работ",
                        "text": (
                            "11240/24-АС.ВОР\n"
                            "1.3. Устройство постели из песка для кабельной линии\n"
                            "1.5. Укрытие кабельных линий защитными плитами\n"
                        ),
                    }
                ],
            },
            {
                "filename": "Том ЭП.pdf",
                "pages": [
                    {
                        "page": 31,
                        "page_type": "Ведомость объемов работ",
                        "text": (
                            "11240/24-ЭП.ВОР\n"
                            "2.3. Устройство песчаной подсыпки\n"
                            "2.8. Армирование фундаментной плиты\n"
                        ),
                    }
                ],
            },
        ]
    }
    (analysis_path / "page_analysis.json").write_text(
        json.dumps(page_analysis, ensure_ascii=False), encoding="utf-8"
    )

    result = registry.analyze_project("TEST_PROJECT")

    assert result["acts_count"] == 0
    assert result["acts"] == []
    assert result["review_candidates_count"] == 1
    assert result["requires_field_confirmation"] is True
    assert result["review_candidates"][0]["code"] == "cable_trench"
    assert result["review_candidates"][0]["status"] == "Требует проверки по факту"
    assert result["review_candidates"][0]["evidence"] == [
        {
            "document": "Том АС.pdf",
            "page": 37,
            "work_item": "1.3",
            "matched_phrase": "постели из песка для кабельной линии",
        },
        {
            "document": "Том АС.pdf",
            "page": 37,
            "work_item": "1.5",
            "matched_phrase": "укрытие кабельных линий защитными плитами",
        },
    ]


def test_work_volume_candidate_requires_both_work_items(monkeypatch, tmp_path):
    registry = HiddenWorksRegistry()
    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"
    analysis_path.mkdir(parents=True)

    monkeypatch.setattr(registry, "_project_path", lambda _: project_path)
    monkeypatch.setattr(registry, "_analysis_path", lambda _: analysis_path)
    monkeypatch.setattr(registry, "_extract_register_entries", lambda _: [])

    (analysis_path / "page_analysis.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "filename": "Том АС.pdf",
                        "pages": [
                            {
                                "page": 37,
                                "page_type": "Ведомость объемов работ",
                                "text": (
                                    "11240/24-АС.ВОР\n"
                                    "1.3. Устройство постели из песка для кабельной линии\n"
                                ),
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = registry.analyze_project("TEST_PROJECT")

    assert result["review_candidates_count"] == 0


def test_work_volume_candidate_keeps_documents_separate(monkeypatch, tmp_path):
    registry = HiddenWorksRegistry()
    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"
    analysis_path.mkdir(parents=True)

    monkeypatch.setattr(registry, "_project_path", lambda _: project_path)
    monkeypatch.setattr(registry, "_analysis_path", lambda _: analysis_path)
    monkeypatch.setattr(registry, "_extract_register_entries", lambda _: [])

    documents = [
        {
            "filename": filename,
            "pages": [
                {
                    "page": 1,
                    "page_type": "Ведомость объемов работ",
                    "text": f"11240/24-АС.ВОР\n{item}",
                }
            ],
        }
        for filename, item in (
            (
                "Первый том.pdf",
                "1.3. Устройство постели из песка для кабельной линии",
            ),
            (
                "Другой том.pdf",
                "1.5. Укрытие кабельных линий защитными плитами",
            ),
        )
    ]
    (analysis_path / "page_analysis.json").write_text(
        json.dumps({"documents": documents}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = registry.analyze_project("TEST_PROJECT")

    assert result["acts_count"] == 0
    assert result["review_candidates_count"] == 0


def test_work_volume_reference_in_notes_is_not_a_document_designation(
    monkeypatch, tmp_path
):
    registry = HiddenWorksRegistry()
    project_path = tmp_path / "TEST_PROJECT"
    analysis_path = project_path / "analysis"
    analysis_path.mkdir(parents=True)

    monkeypatch.setattr(registry, "_project_path", lambda _: project_path)
    monkeypatch.setattr(registry, "_analysis_path", lambda _: analysis_path)
    monkeypatch.setattr(registry, "_extract_register_entries", lambda _: [])

    (analysis_path / "page_analysis.json").write_text(
        json.dumps(
            {
                "documents": [{
                    "filename": "Том АС.pdf",
                    "pages": [{
                        "page": 37,
                        "page_type": "Ведомость объемов работ",
                        "text": (
                            "Ссылка на 11240/24-АС.ВОР в примечании\n"
                            "1.3. Устройство постели из песка для кабельной линии\n"
                            "1.5. Укрытие кабельных линий защитными плитами\n"
                        ),
                    }],
                }]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert registry.analyze_project("TEST_PROJECT")["review_candidates_count"] == 0
