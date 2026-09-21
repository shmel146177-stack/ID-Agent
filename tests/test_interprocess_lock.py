from threading import Event, Thread

from app.services.interprocess_lock import exclusive_file_lock


def test_exclusive_file_lock_serializes_independent_callers(tmp_path):
    lock_path = str(tmp_path / "review.lock")
    first_acquired = Event()
    release_first = Event()
    second_started = Event()
    second_acquired = Event()

    def hold_first_lock():
        with exclusive_file_lock(lock_path):
            first_acquired.set()
            release_first.wait(timeout=2)

    def wait_for_second_lock():
        second_started.set()

        with exclusive_file_lock(lock_path):
            second_acquired.set()

    first = Thread(target=hold_first_lock)
    second = Thread(target=wait_for_second_lock)
    first.start()
    assert first_acquired.wait(timeout=2)

    second.start()
    assert second_started.wait(timeout=2)
    assert not second_acquired.wait(timeout=0.1)

    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert second_acquired.is_set()
