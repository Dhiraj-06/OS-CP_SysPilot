"""Metrics calculations for CPU Scheduling algorithms.

Standard OS Formulas:
- Completion Time (CT): Instant process execution terminates.
- Turnaround Time (TAT) = CT - Arrival Time
- Waiting Time (WT) = TAT - Burst Time
- Response Time (RT) = First CPU Execution Time - Arrival Time
- CPU Utilization (%) = (Total Busy Time / Makespan) * 100
- Throughput = Completed Processes / Makespan
- Context Switch Count: Number of CPU handovers between different processes
"""

from typing import List, Dict, Any

class SchedulingMetrics:
    """Calculates and aggregates standard operating system scheduling metrics."""

    @staticmethod
    def compute(processes: List[Dict[str, Any]], timeline: List[Dict[str, Any]], makespan: int) -> Dict[str, Any]:
        """Compute comprehensive performance metrics from execution timeline."""
        if not processes or makespan <= 0:
            return {
                "process_metrics": [],
                "avg_waiting_time": 0.0,
                "avg_turnaround_time": 0.0,
                "avg_response_time": 0.0,
                "cpu_utilization": 0.0,
                "throughput": 0.0,
                "context_switches": 0,
                "makespan": makespan
            }

        # Track first execution time and completion time from timeline
        first_executed = {}
        completion_times = {}
        context_switches = 0
        last_pid = None
        busy_time = 0

        for block in timeline:
            pid = block.get("pid")
            start = block.get("start", 0)
            end = block.get("end", 0)
            duration = end - start

            if pid is not None and pid != "IDLE":
                busy_time += duration
                if pid not in first_executed:
                    first_executed[pid] = start
                completion_times[pid] = max(completion_times.get(pid, 0), end)
                if last_pid is not None and last_pid != pid and last_pid != "IDLE":
                    context_switches += 1
                last_pid = pid
            elif pid == "IDLE":
                last_pid = "IDLE"

        proc_metrics = []
        total_wt = 0.0
        total_tat = 0.0
        total_rt = 0.0

        for p in processes:
            pid = p["pid"]
            arrival = p["arrival_time"]
            burst = p["burst_time"]
            ct = completion_times.get(pid, arrival + burst)
            tat = ct - arrival
            wt = tat - burst
            rt = first_executed.get(pid, arrival) - arrival

            total_wt += wt
            total_tat += tat
            total_rt += rt

            proc_metrics.append({
                "pid": pid,
                "name": p.get("name", f"P{pid}"),
                "arrival_time": arrival,
                "burst_time": burst,
                "priority": p.get("priority", 0),
                "completion_time": ct,
                "turnaround_time": tat,
                "waiting_time": wt,
                "response_time": rt
            })

        n = len(processes)
        avg_wt = round(total_wt / n, 2)
        avg_tat = round(total_tat / n, 2)
        avg_rt = round(total_rt / n, 2)
        cpu_util = round((busy_time / makespan) * 100, 2) if makespan > 0 else 0.0
        throughput = round(n / makespan, 4) if makespan > 0 else 0.0

        return {
            "process_metrics": proc_metrics,
            "avg_waiting_time": avg_wt,
            "avg_turnaround_time": avg_tat,
            "avg_response_time": avg_rt,
            "cpu_utilization": cpu_util,
            "throughput": throughput,
            "context_switches": context_switches,
            "makespan": makespan
        }
