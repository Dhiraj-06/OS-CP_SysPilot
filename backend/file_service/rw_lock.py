"""Thread-Safe Reader-Writer Lock with Writer Preference.

OS Concurrency Design:
- Multiple reader threads can acquire the lock simultaneously for shared reading.
- Only one writer thread can acquire the lock for exclusive writing.
- Prevents writer starvation: If one or more writers are waiting to acquire the lock,
  new incoming readers are placed on wait, allowing queued writers to proceed.
"""

import threading
from typing import Dict

class RWLock:
    """Fair Reader-Writer Lock with Writer Preference."""

    def __init__(self):
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._write_ready = threading.Condition(self._lock)

        self._readers = 0
        self._writers = 0
        self._waiting_writers = 0

    def acquire_read(self):
        """Acquire shared read lock. Waits if a writer is active or waiting."""
        with self._lock:
            while self._writers > 0 or self._waiting_writers > 0:
                self._read_ready.wait()
            self._readers += 1

    def release_read(self):
        """Release shared read lock. Wakes waiting writers when reader count drops to 0."""
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_ready.notify()

    def acquire_write(self):
        """Acquire exclusive write lock. Waits until all active readers and writers finish."""
        with self._lock:
            self._waiting_writers += 1
            while self._readers > 0 or self._writers > 0:
                self._write_ready.wait()
            self._waiting_writers -= 1
            self._writers += 1

    def release_write(self):
        """Release exclusive write lock. Wakes waiting writers or queued readers."""
        with self._lock:
            self._writers -= 1
            if self._waiting_writers > 0:
                self._write_ready.notify()
            else:
                self._read_ready.notify_all()


class FileLockManager:
    """Manages fine-grained RWLocks per individual file."""

    def __init__(self):
        self._locks: Dict[str, RWLock] = {}
        self._global_lock = threading.Lock()

    def get_lock(self, filename: str) -> RWLock:
        """Retrieve or create the unique RWLock for a given file."""
        with self._global_lock:
            if filename not in self._locks:
                self._locks[filename] = RWLock()
            return self._locks[filename]
