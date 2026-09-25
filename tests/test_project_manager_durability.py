import importlib
import multiprocessing
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.project_manager import ProjectManager


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("failure_stage", ["dump", "fsync", "replace"])
def test_failed_card_write_preserves_previous_state(
    tmp_path, monkeypatch, operation, failure_stage
):
    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    card_path = tmp_path / "TEST_PROJECT" / "project.json"
    before = None
    if operation == "update":
        manager.create_project("TEST_PROJECT")
        manager.update_project("TEST_PROJECT", {"customer": "Saved customer"})
        before = card_path.read_bytes()

    def fail(*args, **kwargs):
        if failure_stage == "dump":
            args[1].write("{")
        raise OSError("Simulated write failure")

    atomic = importlib.import_module("app.services.atomic_json")
    owner = atomic.json if failure_stage == "dump" else atomic.os
    with monkeypatch.context() as failing:
        failing.setattr(owner, failure_stage, fail)
        with pytest.raises(OSError, match="Simulated write failure"):
            if operation == "create":
                manager.create_project("TEST_PROJECT")
            else:
                manager.update_project("TEST_PROJECT", {"address": "New address"})

    if before is None:
        assert not card_path.exists()
    else:
        assert card_path.read_bytes() == before
    assert not list(card_path.parent.glob("*.tmp"))

    # A failed write must also release the lock so the operation can be retried.
    manager.create_project("TEST_PROJECT")
    manager.update_project("TEST_PROJECT", {"address": "New address"})
    saved = manager.get_project("TEST_PROJECT")
    assert saved["address"] == "New address"
    if before is not None:
        assert saved["customer"] == "Saved customer"


def _mutate_card(root, operation, started, paused, release, completed):
    manager = ProjectManager()
    manager.projects_root = root
    module = importlib.import_module("app.services.project_manager")
    write = module.write_json_atomically

    def pause_before_write(path, data):
        paused.set()
        if not release.wait(timeout=15):
            raise TimeoutError("Card write was not released")
        write(path, data)

    started.set()
    if paused is not None:
        with patch.object(module, "write_json_atomically", pause_before_write):
            manager.update_project("TEST_PROJECT", {"customer": "Customer A"})
    elif operation == "update":
        manager.update_project("TEST_PROJECT", {"address": "Address B"})
    else:
        result = manager.create_project("TEST_PROJECT")
        assert result["customer"] == "Customer A"
    completed.set()


@pytest.mark.parametrize("second_operation", ["update", "create"])
def test_card_mutations_serialize_across_processes(tmp_path, second_operation):
    manager = ProjectManager()
    manager.projects_root = str(tmp_path)
    manager.create_project("TEST_PROJECT")
    context = multiprocessing.get_context("spawn")
    paused = context.Event()
    release = context.Event()
    first_done = context.Event()
    second_started = context.Event()
    second_done = context.Event()
    first = context.Process(
        target=_mutate_card,
        args=(str(tmp_path), "update", context.Event(), paused, release, first_done),
    )
    second = context.Process(
        target=_mutate_card,
        args=(str(tmp_path), second_operation, second_started, None, None, second_done),
    )
    processes = []
    try:
        first.start()
        processes.append(first)
        assert paused.wait(timeout=10)
        second.start()
        processes.append(second)
        assert second_started.wait(timeout=10)
        assert not second_done.wait(timeout=0.2)
        release.set()
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
    finally:
        release.set()
        for process in processes:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

    assert first_done.is_set()
    assert second_done.is_set()
    saved = manager.get_project("TEST_PROJECT")
    assert saved["customer"] == "Customer A"
    if second_operation == "update":
        assert saved["address"] == "Address B"
    assert not list((Path(tmp_path) / "TEST_PROJECT").glob("*.tmp"))
