"""Unit tests for CPU Scheduling algorithms and metrics."""

import pytest
from backend.scheduler.algorithms import (
    fcfs, sjf_non_preemptive, srtf_preemptive,
    priority_non_preemptive, round_robin, mlfq
)
from backend.scheduler.metrics import SchedulingMetrics
from backend.scheduler.recommender import SchedulingRecommender

@pytest.fixture
def textbook_workload():
    """Standard OS textbook process set."""
    return [
        {"pid": 1, "name": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
        {"pid": 2, "name": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1},
        {"pid": 3, "name": "P3", "arrival_time": 2, "burst_time": 8, "priority": 4},
        {"pid": 4, "name": "P4", "arrival_time": 3, "burst_time": 2, "priority": 3},
        {"pid": 5, "name": "P5", "arrival_time": 4, "burst_time": 4, "priority": 2}
    ]

def test_fcfs(textbook_workload):
    res = fcfs(textbook_workload)
    assert res["makespan"] == 22
    metrics = SchedulingMetrics.compute(textbook_workload, res["timeline"], res["makespan"])
    assert metrics["cpu_utilization"] == 100.0
    assert len(metrics["process_metrics"]) == 5
    assert metrics["avg_turnaround_time"] > 0
    assert metrics["avg_waiting_time"] > 0

def test_sjf_non_preemptive(textbook_workload):
    res = sjf_non_preemptive(textbook_workload)
    assert res["makespan"] == 22
    metrics = SchedulingMetrics.compute(textbook_workload, res["timeline"], res["makespan"])
    assert metrics["cpu_utilization"] == 100.0

def test_srtf_preemptive(textbook_workload):
    res = srtf_preemptive(textbook_workload)
    assert res["makespan"] == 22
    metrics = SchedulingMetrics.compute(textbook_workload, res["timeline"], res["makespan"])
    # SRTF should have lower or equal average waiting time compared to FCFS
    fcfs_res = fcfs(textbook_workload)
    fcfs_metrics = SchedulingMetrics.compute(textbook_workload, fcfs_res["timeline"], fcfs_res["makespan"])
    assert metrics["avg_waiting_time"] <= fcfs_metrics["avg_waiting_time"]

def test_round_robin(textbook_workload):
    res = round_robin(textbook_workload, quantum=2)
    assert res["makespan"] == 22
    metrics = SchedulingMetrics.compute(textbook_workload, res["timeline"], res["makespan"])
    assert metrics["context_switches"] > 0

def test_mlfq(textbook_workload):
    res = mlfq(textbook_workload, q0_quantum=2, q1_quantum=4, boost_interval=20)
    assert res["makespan"] == 22

def test_recommender(textbook_workload):
    rec = SchedulingRecommender()
    recommendation = rec.recommend(textbook_workload)
    assert "recommended_algorithm" in recommendation
    assert "workload_profile" in recommendation
    assert len(recommendation["leaderboard"]) > 0
