"""Unit tests for Dijkstra's Banker's Algorithm."""

import pytest
from backend.concurrency.bankers_algorithm import BankersAlgorithm

@pytest.fixture
def classic_safe_state():
    """Silberschatz classic 5-process 3-resource safe state."""
    available = [3, 3, 2]
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]
    max_matrix = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]
    return available, allocation, max_matrix

def test_bankers_safe_state(classic_safe_state):
    avail, alloc, max_m = classic_safe_state
    res = BankersAlgorithm.is_safe_state(avail, alloc, max_m)
    assert res["is_safe"] is True
    assert len(res["safe_sequence"]) == 5
    # P1 can finish first since Need[1] = [1, 2, 2] <= [3, 3, 2]
    assert res["safe_sequence"][0] == "P1"

def test_bankers_unsafe_state():
    # Depleted available vector causing deadlock
    avail = [0, 0, 0]
    alloc = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]
    max_m = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [4, 2, 2],
        [4, 3, 3]
    ]
    res = BankersAlgorithm.is_safe_state(avail, alloc, max_m)
    assert res["is_safe"] is False
    assert len(res["deadlocked_processes"]) > 0

def test_bankers_resource_request(classic_safe_state):
    avail, alloc, max_m = classic_safe_state
    # P1 requests [1, 0, 2]
    req_res = BankersAlgorithm.request_resources(1, [1, 0, 2], avail, alloc, max_m)
    assert req_res["granted"] is True

    # P4 requests [3, 3, 0] which exceeds available [3, 3, 2] in resource B
    req_res2 = BankersAlgorithm.request_resources(4, [3, 3, 0], avail, alloc, max_m)
    assert req_res2["granted"] is False
