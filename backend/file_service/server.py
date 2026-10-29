"""Multi-Client Concurrent File Service.

Coordinates:
- Thread-safe Reader-Writer locks per file (shared reads, exclusive writes)
- Simulated OS LRU Page Cache
- Concurrent client operation logging and statistics
- Persistent file storage
"""

from pathlib import Path
import threading
import time
import socket
from typing import Dict, Any, List, Optional
from ..config import FILE_SERVICE_STORAGE, FILE_SERVICE_PORT
from .rw_lock import FileLockManager
from .page_cache import PageCache

class ConcurrentFileServer:
    """Manages concurrent file read/write operations across multiple clients."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or FILE_SERVICE_STORAGE
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.lock_manager = FileLockManager()
        self.cache = PageCache(capacity=8, storage_dir=self.storage_dir)
        self.activity_log: List[Dict[str, Any]] = []
        self._log_lock = threading.Lock()
        self.active_readers: Dict[str, int] = {}
        self.active_writers: Dict[str, int] = {}
        self._state_lock = threading.Lock()

    def read_file(self, client_id: str, filename: str) -> Dict[str, Any]:
        """Concurrent shared read operation."""
        lock = self.lock_manager.get_lock(filename)
        start_time = time.perf_counter()

        with self._state_lock:
            self.active_readers[filename] = self.active_readers.get(filename, 0) + 1

        lock.acquire_read()
        try:
            # Try page cache first
            source = "CACHE"
            content = self.cache.get(filename)
            if content is None:
                # Cache miss: read from disk
                source = "DISK"
                disk_path = self.storage_dir / filename
                if disk_path.exists():
                    with open(disk_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Populate page cache (clean page)
                    self.cache.put(filename, content, is_dirty=False)
                else:
                    content = ""

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._log_event(client_id, "READ", filename, f"Read {len(content)} chars from {source}", elapsed_ms)

            return {
                "success": True,
                "filename": filename,
                "content": content,
                "source": source,
                "latency_ms": round(elapsed_ms, 2)
            }
        finally:
            lock.release_read()
            with self._state_lock:
                self.active_readers[filename] = max(0, self.active_readers.get(filename, 1) - 1)

    def write_file(self, client_id: str, filename: str, content: str) -> Dict[str, Any]:
        """Concurrent exclusive write operation."""
        lock = self.lock_manager.get_lock(filename)
        start_time = time.perf_counter()

        with self._state_lock:
            self.active_writers[filename] = self.active_writers.get(filename, 0) + 1

        lock.acquire_write()
        try:
            # Update cache as dirty
            self.cache.put(filename, content, is_dirty=True)
            # Write through to storage
            disk_path = self.storage_dir / filename
            with open(disk_path, "w", encoding="utf-8") as f:
                f.write(content)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._log_event(client_id, "WRITE", filename, f"Overwrote {len(content)} chars", elapsed_ms)

            return {
                "success": True,
                "filename": filename,
                "size_written": len(content),
                "latency_ms": round(elapsed_ms, 2)
            }
        finally:
            lock.release_write()
            with self._state_lock:
                self.active_writers[filename] = max(0, self.active_writers.get(filename, 1) - 1)

    def append_file(self, client_id: str, filename: str, addition: str) -> Dict[str, Any]:
        """Concurrent exclusive append operation."""
        lock = self.lock_manager.get_lock(filename)
        start_time = time.perf_counter()

        with self._state_lock:
            self.active_writers[filename] = self.active_writers.get(filename, 0) + 1

        lock.acquire_write()
        try:
            # Read existing
            current = self.cache.get(filename)
            if current is None:
                disk_path = self.storage_dir / filename
                if disk_path.exists():
                    with open(disk_path, "r", encoding="utf-8") as f:
                        current = f.read()
                else:
                    current = ""

            updated = current + ("\n" if current and not current.endswith("\n") else "") + addition
            self.cache.put(filename, updated, is_dirty=True)

            disk_path = self.storage_dir / filename
            with open(disk_path, "w", encoding="utf-8") as f:
                f.write(updated)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self._log_event(client_id, "APPEND", filename, f"Appended '{addition[:30]}...'", elapsed_ms)

            return {
                "success": True,
                "filename": filename,
                "new_total_size": len(updated),
                "latency_ms": round(elapsed_ms, 2)
            }
        finally:
            lock.release_write()
            with self._state_lock:
                self.active_writers[filename] = max(0, self.active_writers.get(filename, 1) - 1)

    def list_files(self) -> List[Dict[str, Any]]:
        """List all files currently in persistent storage."""
        files = []
        for p in self.storage_dir.glob("*"):
            if p.is_file():
                files.append({
                    "filename": p.name,
                    "size_bytes": p.stat().st_size,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))
                })
        return files

    def get_status(self) -> Dict[str, Any]:
        """Consolidate service health, active lock counters, and cache status."""
        with self._state_lock:
            readers_copy = {k: v for k, v in self.active_readers.items() if v > 0}
            writers_copy = {k: v for k, v in self.active_writers.items() if v > 0}

        return {
            "storage_directory": str(self.storage_dir),
            "total_files": len(list(self.storage_dir.glob("*"))),
            "active_readers": readers_copy,
            "active_writers": writers_copy,
            "cache_stats": self.cache.get_stats(),
            "recent_activity": self.get_activity_log(limit=25)
        }

    def _log_event(self, client_id: str, op: str, filename: str, details: str, latency_ms: float):
        with self._log_lock:
            self.activity_log.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "client_id": client_id,
                "operation": op,
                "filename": filename,
                "details": details,
                "latency_ms": round(latency_ms, 2)
            })
            if len(self.activity_log) > 100:
                self.activity_log.pop(0)

    def get_activity_log(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self._log_lock:
            return list(reversed(self.activity_log[-limit:]))
