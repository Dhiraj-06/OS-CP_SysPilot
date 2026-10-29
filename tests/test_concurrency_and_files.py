"""Unit tests for Concurrency, RWLock, LRU Page Cache, and File Service."""

import pytest
import tempfile
from pathlib import Path
from backend.file_service.rw_lock import RWLock
from backend.file_service.page_cache import PageCache
from backend.file_service.server import ConcurrentFileServer
from backend.concurrency.synchronization import BoundedBufferSimulator

def test_bounded_buffer():
    sim = BoundedBufferSimulator(capacity=4)
    res = sim.run_simulation(num_producers=2, num_consumers=2, operations_per_worker=3)
    assert res["total_produced"] == 6
    assert res["total_consumed"] == 6
    assert len(res["final_buffer"]) == 0

def test_rw_lock_basic():
    rw = RWLock()
    # Acquire and release read
    rw.acquire_read()
    rw.release_read()

    # Acquire and release write
    rw.acquire_write()
    rw.release_write()

def test_page_cache_lru():
    cache = PageCache(capacity=3)
    cache.put("f1.txt", "data1")
    cache.put("f2.txt", "data2")
    cache.put("f3.txt", "data3")

    # All should be in cache
    assert cache.get("f1.txt") == "data1"
    assert cache.hits == 1

    # Adding f4 should evict f2 (since f1 was just read)
    cache.put("f4.txt", "data4")
    assert cache.get("f2.txt") is None
    assert cache.misses == 1
    assert cache.evictions == 1

def test_concurrent_file_server():
    with tempfile.TemporaryDirectory() as tmp_dir:
        srv = ConcurrentFileServer(storage_dir=Path(tmp_dir))
        
        # Write
        w_res = srv.write_file("client_1", "notes.txt", "Hello OS")
        assert w_res["success"] is True

        # Read
        r_res = srv.read_file("client_2", "notes.txt")
        assert r_res["success"] is True
        assert r_res["content"] == "Hello OS"

        # Append
        a_res = srv.append_file("client_3", "notes.txt", "Second Line")
        assert a_res["success"] is True

        # Read updated
        r_res2 = srv.read_file("client_4", "notes.txt")
        assert "Second Line" in r_res2["content"]
