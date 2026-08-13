import app.api.project_processor as api_module


def test_project_api_create_and_list_projects(monkeypatch):

    created_project = {
        "project_name": "TEST_PROJECT",
        "object_name": "",
    }

    monkeypatch.setattr(
        api_module.project_manager,
        "create_project",
        lambda name: created_project,
    )

    create_data = api_module.ProjectCreate(
        project_name="TEST_PROJECT",
    )

    create_result = api_module.create_project(
        create_data
    )

    assert create_result["project"] == created_project
    assert "status" in create_result

    projects = [
        {
            "project_name": "TEST_PROJECT",
        },
        {
            "project_name": "SECOND_PROJECT",
        },
    ]

    monkeypatch.setattr(
        api_module.project_manager,
        "list_projects",
        lambda: projects,
    )

    list_result = api_module.list_projects()

    assert list_result["projects_count"] == 2
    assert list_result["projects"] == projects
