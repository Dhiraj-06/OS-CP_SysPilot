"""Simulated OS Page / Buffer Cache with LRU Eviction Policy.

Operating System Principles:
- Emulates the Linux Page Cache layer between file I/O operations and disk storage.
- Implements LRU (Least Recently Used) page eviction algorithm.
- Tracks 'Dirty Pages' (modified in memory but not yet written to disk).
- Simulates kernel background writeback (pdflush daemon).
"""

from collections import OrderedDict
from pathlib import Path
import threading
import time
from typing import Optional, Dict, Any

class PageCache:
    """Thread-safe LRU Page Cache simulating OS buffer cache."""

    def __init__(self, capacity: int = 8, storage_dir: Optional[Path] = None):
        self.capacity = capacity
        self.storage_dir = storage_dir
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = threading.Lock()

        # Telemetry stats
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.flushes = 0

    def get(self, filename: str) -> Optional[str]:
        """Read file content from cache; moves page to MRU position."""
        with self.lock:
            if filename in self.cache:
                self.hits += 1
                # Mark as most recently used
                self.cache.move_to_end(filename)
                return self.cache[filename]["content"]
            else:
                self.misses += 1
                return None

    def put(self, filename: str, content: str, is_dirty: bool = False):
        """Put or update a page in the cache; evicts LRU page if full."""
        with self.lock:
            if filename in self.cache:
                self.cache.move_to_end(filename)
                self.cache[filename]["content"] = content
                self.cache[filename]["dirty"] = is_dirty
                self.cache[filename]["updated_at"] = time.time()
                return

            # Check capacity
            if len(self.cache) >= self.capacity:
                self._evict_lru()

            self.cache[filename] = {
                "content": content,
                "dirty": is_dirty,
                "updated_at": time.time()
            }

    def _evict_lru(self):
        """Evict the least recently used page; flush to disk if dirty."""
        oldest_filename, page = self.cache.popitem(last=False)
        self.evictions += 1
        if page["dirty"] and self.storage_dir:
            self._write_to_disk(oldest_filename, page["content"])
            self.flushes += 1

    def flush_dirty_pages(self) -> int:
        """Write all dirty pages to disk (simulates OS sync / pdflush)."""
        flushed_count = 0
        with self.lock:
            for fname, page in self.cache.items():
                if page["dirty"]:
                    if self.storage_dir:
                        self._write_to_disk(fname, page["content"])
                    page["dirty"] = False
                    flushed_count += 1
            self.flushes += flushed_count
        return flushed_count

    def _write_to_disk(self, filename: str, content: str):
        """Write content directly to persistent disk file."""
        if not self.storage_dir:
            return
        try:
            file_path = self.storage_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics and current page table."""
        with self.lock:
            total_reqs = self.hits + self.misses
            hit_ratio = round((self.hits / total_reqs * 100), 2) if total_reqs > 0 else 0.0

            pages = []
            for fname, item in reversed(self.cache.items()): # MRU to LRU order
                pages.append({
                    "filename": fname,
                    "dirty": item["dirty"],
                    "size_bytes": len(item["content"].encode("utf-8")),
                    "last_accessed": time.strftime("%H:%M:%S", time.localtime(item["updated_at"]))
                })

            return {
                "capacity": self.capacity,
                "current_size": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio_percent": hit_ratio,
                "evictions": self.evictions,
                "flushes": self.flushes,
                "cached_pages": pages
            }
