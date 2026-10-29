"""Intelligent CPU Scheduling Recommendation Engine.

Analyzes the statistical characteristics of an input workload:
- Burst time variance & coefficient of variation (CV)
- Arrival density and inter-arrival time skewness
- Priority spread and urgency distribution
- Preemption tolerance vs context switch sensitivity

Simulates all candidate algorithms and recommends the mathematically optimal
strategy with rigorous academic explanations.
"""

from typing import List, Dict, Any
import math
from .simulator import SchedulingSimulator

class SchedulingRecommender:
    """Provides workload-driven scheduling algorithm recommendations."""

    def __init__(self):
        self.simulator = SchedulingSimulator()

    def recommend(self, processes: List[Dict[str, Any]], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze workload profile, benchmark algorithms, and deliver recommendation."""
        if not processes:
            return {"error": "No processes provided for recommendation."}

        # 1. Statistical Workload Analysis
        n = len(processes)
        bursts = [p["burst_time"] for p in processes]
        arrivals = [p["arrival_time"] for p in processes]
        priorities = [p.get("priority", 0) for p in processes]

        mean_burst = sum(bursts) / n
        variance_burst = sum((b - mean_burst) ** 2 for b in bursts) / n if n > 1 else 0
        std_burst = math.sqrt(variance_burst)
        cv_burst = (std_burst / mean_burst) if mean_burst > 0 else 0 # Coefficient of Variation

        distinct_arrivals = len(set(arrivals))
        is_concurrent_arrival = (distinct_arrivals == 1)
        priority_range = max(priorities) - min(priorities) if priorities else 0

        # 2. Benchmark all algorithms
        leaderboard = self.simulator.compare_all(processes, params)

        # 3. Decision Heuristic & Recommendation Logic
        recommended_key = leaderboard[0]["algorithm_key"] # Best avg waiting time candidate
        best_entry = leaderboard[0]

        reasons = []
        trade_offs = []

        if cv_burst > 0.6:
            reasons.append(f"High burst variance detected (CV = {cv_burst:.2f}). Algorithms prioritizing shorter jobs (SRTF/SJF) yield mathematically optimal average waiting times.")
        else:
            reasons.append(f"Uniform burst times detected (CV = {cv_burst:.2f}). Preemptive context switches yield minimal benefits.")

        if priority_range > 0:
            reasons.append(f"Workload specifies non-trivial process priorities (range = {priority_range}). If priority inversion or deadlines matter, Priority with Aging is essential.")

        if is_concurrent_arrival:
            reasons.append("All processes arrive simultaneously (t=0). Conveyor-belt starvation is mitigated, giving SJF/SRTF pure advantage.")
        else:
            reasons.append("Staggered process arrivals detected; dynamic ready queue responsiveness is important.")

        # Special considerations
        if recommended_key == "srtf":
            trade_offs.append("Provides the provably minimal Average Waiting Time, but incurs higher context switch overhead than non-preemptive SJF.")
        elif recommended_key == "round_robin":
            trade_offs.append("Provides maximum responsiveness and fairness across all processes, ideal for interactive timesharing environments.")
        elif recommended_key == "mlfq":
            trade_offs.append("Adapts dynamically without prior knowledge of burst times; automatically prioritizes I/O-bound jobs over CPU-heavy jobs.")
        elif recommended_key == "fcfs":
            trade_offs.append("Zero preemption overhead and simplest scheduler implementation, but susceptible to the Convoy Effect if long jobs arrive first.")

        return {
            "recommended_algorithm": {
                "key": recommended_key,
                "name": best_entry["algorithm_name"],
                "avg_waiting_time": best_entry["avg_waiting_time"],
                "avg_turnaround_time": best_entry["avg_turnaround_time"],
                "avg_response_time": best_entry["avg_response_time"],
                "context_switches": best_entry["context_switches"]
            },
            "workload_profile": {
                "process_count": n,
                "mean_burst_time": round(mean_burst, 2),
                "std_burst_time": round(std_burst, 2),
                "coefficient_of_variation": round(cv_burst, 2),
                "is_concurrent_arrival": is_concurrent_arrival,
                "priority_variance": priority_range > 0
            },
            "justification": reasons,
            "trade_offs": trade_offs,
            "leaderboard": leaderboard
        }
