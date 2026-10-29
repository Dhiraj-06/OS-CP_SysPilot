"""CPU Scheduling Simulation Engine.

Orchestrates execution of scheduling algorithms, timeline tracking,
and comparative benchmarking across all supported algorithms.
"""

from typing import List, Dict, Any
from .algorithms import (
    fcfs, sjf_non_preemptive, srtf_preemptive,
    priority_non_preemptive, priority_preemptive_aging,
    round_robin, mlfq
)
from .metrics import SchedulingMetrics

ALGORITHM_MAP = {
    "fcfs": ("First-Come First-Served", fcfs),
    "sjf": ("Shortest Job First (Non-preemptive)", sjf_non_preemptive),
    "srtf": ("Shortest Remaining Time First (Preemptive)", srtf_preemptive),
    "priority_np": ("Priority (Non-preemptive)", priority_non_preemptive),
    "priority_preemptive": ("Priority (Preemptive with Aging)", priority_preemptive_aging),
    "round_robin": ("Round Robin", round_robin),
    "mlfq": ("Multi-Level Feedback Queue", mlfq)
}

class SchedulingSimulator:
    """Runs simulations and comparative analyses."""

    def run_algorithm(self, algo_key: str, processes: List[Dict[str, Any]], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single scheduling algorithm on a process set."""
        if algo_key not in ALGORITHM_MAP:
            raise ValueError(f"Unknown algorithm: {algo_key}. Supported: {list(ALGORITHM_MAP.keys())}")

        name, func = ALGORITHM_MAP[algo_key]
        params = params or {}

        # Call with appropriate parameters
        if algo_key == "round_robin":
            quantum = params.get("quantum", 2)
            result = func(processes, quantum=quantum)
        elif algo_key == "mlfq":
            q0 = params.get("q0_quantum", 2)
            q1 = params.get("q1_quantum", 4)
            boost = params.get("boost_interval", 20)
            result = func(processes, q0_quantum=q0, q1_quantum=q1, boost_interval=boost)
        elif algo_key == "priority_preemptive":
            aging = params.get("aging_rate", 1)
            result = func(processes, aging_rate=aging)
        else:
            result = func(processes)

        timeline = result["timeline"]
        makespan = result["makespan"]
        metrics = SchedulingMetrics.compute(processes, timeline, makespan)

        return {
            "algorithm_key": algo_key,
            "algorithm_name": name,
            "timeline": timeline,
            "makespan": makespan,
            "metrics": metrics
        }

    def compare_all(self, processes: List[Dict[str, Any]], params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run all algorithms sequentially on identical workload to compare performance."""
        comparisons = []
        for key in ALGORITHM_MAP.keys():
            try:
                res = self.run_algorithm(key, processes, params)
                m = res["metrics"]
                comparisons.append({
                    "algorithm_key": key,
                    "algorithm_name": res["algorithm_name"],
                    "avg_waiting_time": m["avg_waiting_time"],
                    "avg_turnaround_time": m["avg_turnaround_time"],
                    "avg_response_time": m["avg_response_time"],
                    "cpu_utilization": m["cpu_utilization"],
                    "context_switches": m["context_switches"],
                    "throughput": m["throughput"],
                    "makespan": res["makespan"]
                })
            except Exception as e:
                continue

        # Sort primarily by lowest average waiting time
        comparisons.sort(key=lambda x: x["avg_waiting_time"])
        return comparisons
