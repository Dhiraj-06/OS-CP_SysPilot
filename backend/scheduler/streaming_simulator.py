"""Real-Time Event-Driven Scheduling Simulator.

Transforms batch scheduling algorithms into streaming event generators
that yield step-by-step execution events for live frontend visualization.

Events emitted:
- PROCESS_ARRIVED
- PROCESS_QUEUED
- PROCESS_STARTED
- PROCESS_RESUMED
- PROCESS_PREEMPTED
- PROCESS_COMPLETED
- CONTEXT_SWITCH
- CPU_IDLE
- TIME_QUANTUM_EXPIRED
- PRIORITY_CHANGED
- QUEUE_CHANGED (MLFQ)
"""

from typing import List, Dict, Any, Generator
from copy import deepcopy
import time


class StreamingSimulator:
    """Event-driven scheduler that yields real-time simulation events."""

    def __init__(self):
        self.current_time = 0
        self.makespan = 0

    def simulate(
        self,
        algorithm: str,
        processes: List[Dict[str, Any]],
        params: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generate simulation events step-by-step.

        Yields events with structure:
        {
            "time": float,
            "event": str,
            "pid": int,
            "process": dict,
            "ready_queue": list,
            "running": int or None,
            "completed": list,
            "decision_rationale": str,
            "state_snapshot": dict
        }
        """
        params = params or {}

        if algorithm == "fcfs":
            yield from self._simulate_fcfs(processes)
        elif algorithm == "sjf":
            yield from self._simulate_sjf(processes)
        elif algorithm == "srtf":
            yield from self._simulate_srtf(processes)
        elif algorithm == "priority_np":
            yield from self._simulate_priority_np(processes)
        elif algorithm == "priority_preemptive":
            yield from self._simulate_priority_preemptive(processes, params.get("aging_rate", 1))
        elif algorithm == "round_robin":
            yield from self._simulate_round_robin(processes, params.get("quantum", 2))
        elif algorithm == "mlfq":
            yield from self._simulate_mlfq(
                processes,
                params.get("q0_quantum", 2),
                params.get("q1_quantum", 4),
                params.get("boost_interval", 20)
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def _simulate_fcfs(self, processes: List[Dict[str, Any]]) -> Generator:
        """FCFS: First-Come, First-Served (Non-preemptive)."""
        procs = sorted(deepcopy(processes), key=lambda x: (x["arrival_time"], x["pid"]))
        current_time = 0
        ready_queue = []
        completed = []
        running = None

        unvisited = list(procs)

        while unvisited or running:
            # Check for new arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived at t={current_time}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # If CPU idle and queue has processes
            if not running and ready_queue:
                pid = ready_queue.pop(0)
                running = pid
                p = next(pr for pr in procs if pr["pid"] == pid)

                yield {
                    "time": current_time,
                    "event": "PROCESS_STARTED",
                    "pid": pid,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"FCFS selected P{pid}: first process in ready queue",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # CPU idle with no ready processes
            if not running and not ready_queue and unvisited:
                next_arrival = unvisited[0]["arrival_time"]
                yield {
                    "time": current_time,
                    "event": "CPU_IDLE",
                    "pid": None,
                    "process": None,
                    "ready_queue": [],
                    "running": None,
                    "completed": list(completed),
                    "decision_rationale": f"CPU idle until next arrival at t={next_arrival}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                }
                current_time = next_arrival
                continue

            # Execute running process
            if running:
                p = next(pr for pr in procs if pr["pid"] == running)
                exec_start = current_time
                exec_end = current_time + p["burst_time"]

                # Emit execution progress events
                for t in range(int(exec_start), int(exec_end)):
                    if t > exec_start:
                        yield {
                            "time": t,
                            "event": "PROCESS_EXECUTING",
                            "pid": running,
                            "process": p,
                            "ready_queue": list(ready_queue),
                            "running": running,
                            "completed": list(completed),
                            "remaining_burst": exec_end - t,
                            "decision_rationale": f"P{running} executing (remaining: {exec_end - t})",
                            "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, t)
                        }

                current_time = exec_end
                completed.append(running)

                yield {
                    "time": current_time,
                    "event": "PROCESS_COMPLETED",
                    "pid": running,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": None,
                    "completed": list(completed),
                    "decision_rationale": f"P{running} completed execution",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                }
                running = None

        self.makespan = current_time

    def _simulate_srtf(self, processes: List[Dict[str, Any]]) -> Generator:
        """SRTF: Shortest Remaining Time First (Preemptive)."""
        procs = deepcopy(processes)
        n = len(procs)
        rem_time = {p["pid"]: p["burst_time"] for p in procs}
        current_time = 0
        ready_queue = []
        completed = []
        running = None
        last_running = None

        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

        while len(completed) < n:
            # Check arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived with burst time {p['burst_time']}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Select process with shortest remaining time
            if ready_queue:
                candidates = [pid for pid in ready_queue if rem_time[pid] > 0]
                if candidates:
                    selected = min(candidates, key=lambda pid: (rem_time[pid], pid))

                    # Preemption check
                    if running and running != selected and rem_time[selected] < rem_time[running]:
                        yield {
                            "time": current_time,
                            "event": "PROCESS_PREEMPTED",
                            "pid": running,
                            "process": next(p for p in procs if p["pid"] == running),
                            "ready_queue": list(ready_queue),
                            "running": None,
                            "completed": list(completed),
                            "decision_rationale": f"P{running} preempted: P{selected} has shorter remaining time ({rem_time[selected]} < {rem_time[running]})",
                            "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                        }
                        running = None

                    if not running:
                        ready_queue.remove(selected)
                        running = selected
                        p = next(pr for pr in procs if pr["pid"] == selected)

                        yield {
                            "time": current_time,
                            "event": "PROCESS_STARTED" if last_running != selected else "PROCESS_RESUMED",
                            "pid": selected,
                            "process": p,
                            "ready_queue": list(ready_queue),
                            "running": running,
                            "completed": list(completed),
                            "decision_rationale": f"SRTF selected P{selected}: shortest remaining time ({rem_time[selected]})",
                            "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                        }

            # No ready processes
            if not running and not ready_queue and unvisited:
                next_arrival = unvisited[0]["arrival_time"]
                yield {
                    "time": current_time,
                    "event": "CPU_IDLE",
                    "pid": None,
                    "process": None,
                    "ready_queue": [],
                    "running": None,
                    "completed": list(completed),
                    "decision_rationale": f"CPU idle until t={next_arrival}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                }
                current_time = next_arrival
                continue

            # Execute 1 time unit
            if running:
                rem_time[running] -= 1
                current_time += 1

                yield {
                    "time": current_time,
                    "event": "PROCESS_EXECUTING",
                    "pid": running,
                    "process": next(p for p in procs if p["pid"] == running),
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "remaining_burst": rem_time[running],
                    "decision_rationale": f"P{running} executing (remaining: {rem_time[running]})",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

                if rem_time[running] == 0:
                    completed.append(running)
                    p = next(pr for pr in procs if pr["pid"] == running)

                    yield {
                        "time": current_time,
                        "event": "PROCESS_COMPLETED",
                        "pid": running,
                        "process": p,
                        "ready_queue": list(ready_queue),
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} completed execution",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                    }
                    last_running = running
                    running = None

        self.makespan = current_time

    def _simulate_round_robin(self, processes: List[Dict[str, Any]], quantum: int) -> Generator:
        """Round Robin with configurable time quantum."""
        procs = deepcopy(processes)
        rem_time = {p["pid"]: p["burst_time"] for p in procs}
        current_time = 0
        ready_queue = []
        completed = []
        running = None
        quantum_remaining = 0

        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

        while len(completed) < len(procs):
            # Check arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Select next process if CPU idle
            if not running and ready_queue:
                pid = ready_queue.pop(0)
                running = pid
                quantum_remaining = quantum
                p = next(pr for pr in procs if pr["pid"] == pid)

                yield {
                    "time": current_time,
                    "event": "PROCESS_STARTED",
                    "pid": pid,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Round Robin selected P{pid} (quantum={quantum})",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # CPU idle
            if not running and not ready_queue and unvisited:
                next_arrival = unvisited[0]["arrival_time"]
                current_time = next_arrival
                continue

            # Execute
            if running:
                exec_time = min(rem_time[running], quantum_remaining)
                rem_time[running] -= exec_time
                quantum_remaining -= exec_time
                current_time += exec_time

                yield {
                    "time": current_time,
                    "event": "PROCESS_EXECUTING",
                    "pid": running,
                    "process": next(p for p in procs if p["pid"] == running),
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "remaining_burst": rem_time[running],
                    "quantum_remaining": quantum_remaining,
                    "decision_rationale": f"P{running} executing",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

                # Process completed
                if rem_time[running] == 0:
                    completed.append(running)
                    yield {
                        "time": current_time,
                        "event": "PROCESS_COMPLETED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "ready_queue": list(ready_queue),
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} completed",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                    }
                    running = None
                # Quantum expired
                elif quantum_remaining == 0:
                    ready_queue.append(running)
                    yield {
                        "time": current_time,
                        "event": "TIME_QUANTUM_EXPIRED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "ready_queue": list(ready_queue),
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} time quantum expired, moved to end of queue",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                    }
                    running = None

        self.makespan = current_time

    def _simulate_sjf(self, processes: List[Dict[str, Any]]) -> Generator:
        """SJF: Shortest Job First (Non-preemptive)."""
        # Similar structure to FCFS but selects shortest burst
        procs = deepcopy(processes)
        current_time = 0
        ready_queue = []
        completed = []
        running = None
        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))
        is_completed = {p["pid"]: False for p in procs}

        while len(completed) < len(procs):
            # Arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived with burst {p['burst_time']}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Select shortest job
            if not running and ready_queue:
                ready_queue.sort(key=lambda pid: (next(p["burst_time"] for p in procs if p["pid"] == pid), pid))
                pid = ready_queue.pop(0)
                running = pid
                p = next(pr for pr in procs if pr["pid"] == pid)

                yield {
                    "time": current_time,
                    "event": "PROCESS_STARTED",
                    "pid": pid,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"SJF selected P{pid}: shortest burst time ({p['burst_time']})",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Idle
            if not running and not ready_queue and unvisited:
                current_time = unvisited[0]["arrival_time"]
                continue

            # Execute
            if running:
                p = next(pr for pr in procs if pr["pid"] == running)
                current_time += p["burst_time"]
                completed.append(running)

                yield {
                    "time": current_time,
                    "event": "PROCESS_COMPLETED",
                    "pid": running,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": None,
                    "completed": list(completed),
                    "decision_rationale": f"P{running} completed",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                }
                running = None

        self.makespan = current_time

    def _simulate_priority_np(self, processes: List[Dict[str, Any]]) -> Generator:
        """Priority Scheduling (Non-preemptive)."""
        # Implementation similar to SJF but sorts by priority
        procs = deepcopy(processes)
        current_time = 0
        ready_queue = []
        completed = []
        running = None
        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

        while len(completed) < len(procs):
            # Arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived with priority {p.get('priority', 0)}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Select highest priority (lower number = higher priority)
            if not running and ready_queue:
                ready_queue.sort(key=lambda pid: (next(p.get("priority", 0) for p in procs if p["pid"] == pid), pid))
                pid = ready_queue.pop(0)
                running = pid
                p = next(pr for pr in procs if pr["pid"] == pid)

                yield {
                    "time": current_time,
                    "event": "PROCESS_STARTED",
                    "pid": pid,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Priority selected P{pid}: priority {p.get('priority', 0)}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Idle
            if not running and not ready_queue and unvisited:
                current_time = unvisited[0]["arrival_time"]
                continue

            # Execute
            if running:
                p = next(pr for pr in procs if pr["pid"] == running)
                current_time += p["burst_time"]
                completed.append(running)

                yield {
                    "time": current_time,
                    "event": "PROCESS_COMPLETED",
                    "pid": running,
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": None,
                    "completed": list(completed),
                    "decision_rationale": f"P{running} completed",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                }
                running = None

        self.makespan = current_time

    def _simulate_priority_preemptive(self, processes: List[Dict[str, Any]], aging_rate: int) -> Generator:
        """Priority Scheduling (Preemptive with Aging)."""
        # Similar to SRTF but with priority and aging
        procs = deepcopy(processes)
        n = len(procs)
        rem_time = {p["pid"]: p["burst_time"] for p in procs}
        dynamic_priority = {p["pid"]: p.get("priority", 0) for p in procs}
        waiting_time = {p["pid"]: 0 for p in procs}
        current_time = 0
        ready_queue = []
        completed = []
        running = None

        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

        while len(completed) < n:
            # Arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                ready_queue.append(p["pid"])
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": list(ready_queue),
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} arrived with priority {dynamic_priority[p['pid']]}",
                    "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                }

            # Apply aging to waiting processes
            for pid in ready_queue:
                waiting_time[pid] += 1
                if waiting_time[pid] >= 5:
                    old_priority = dynamic_priority[pid]
                    dynamic_priority[pid] = max(1, dynamic_priority[pid] - aging_rate)
                    if old_priority != dynamic_priority[pid]:
                        yield {
                            "time": current_time,
                            "event": "PRIORITY_CHANGED",
                            "pid": pid,
                            "process": next(p for p in procs if p["pid"] == pid),
                            "ready_queue": list(ready_queue),
                            "running": running,
                            "completed": list(completed),
                            "old_priority": old_priority,
                            "new_priority": dynamic_priority[pid],
                            "decision_rationale": f"P{pid} priority improved by aging: {old_priority} → {dynamic_priority[pid]}",
                            "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                        }
                    waiting_time[pid] = 0

            # Select highest priority
            if ready_queue:
                candidates = [(pid, dynamic_priority[pid]) for pid in ready_queue]
                selected = min(candidates, key=lambda x: (x[1], x[0]))[0]

                # Preemption check
                if running and dynamic_priority[selected] < dynamic_priority[running]:
                    yield {
                        "time": current_time,
                        "event": "PROCESS_PREEMPTED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "ready_queue": list(ready_queue),
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} preempted: P{selected} has higher priority",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                    }
                    running = None

                if not running:
                    ready_queue.remove(selected)
                    running = selected
                    p = next(pr for pr in procs if pr["pid"] == selected)

                    yield {
                        "time": current_time,
                        "event": "PROCESS_STARTED",
                        "pid": selected,
                        "process": p,
                        "ready_queue": list(ready_queue),
                        "running": running,
                        "completed": list(completed),
                        "decision_rationale": f"Priority selected P{selected}: priority {dynamic_priority[selected]}",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, running, completed, current_time)
                    }

            # Idle
            if not running and not ready_queue and unvisited:
                current_time = unvisited[0]["arrival_time"]
                continue

            # Execute
            if running:
                rem_time[running] -= 1
                current_time += 1

                if rem_time[running] == 0:
                    completed.append(running)
                    yield {
                        "time": current_time,
                        "event": "PROCESS_COMPLETED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "ready_queue": list(ready_queue),
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} completed",
                        "state_snapshot": self._get_state_snapshot(procs, ready_queue, None, completed, current_time)
                    }
                    running = None

        self.makespan = current_time

    def _simulate_mlfq(
        self,
        processes: List[Dict[str, Any]],
        q0_quantum: int,
        q1_quantum: int,
        boost_interval: int
    ) -> Generator:
        """Multi-Level Feedback Queue."""
        procs = deepcopy(processes)
        rem_time = {p["pid"]: p["burst_time"] for p in procs}
        proc_queue_level = {p["pid"]: 0 for p in procs}
        current_time = 0
        q0, q1, q2 = [], [], []
        completed = []
        running = None
        quantum_remaining = 0
        last_boost = 0

        unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

        while len(completed) < len(procs):
            # Priority boost
            if boost_interval > 0 and (current_time - last_boost) >= boost_interval:
                moved = q1 + q2
                q0.extend(moved)
                q1.clear()
                q2.clear()
                for pid in moved:
                    proc_queue_level[pid] = 0
                if moved:
                    yield {
                        "time": current_time,
                        "event": "PRIORITY_BOOST",
                        "pids": moved,
                        "ready_queue": q0 + q1 + q2,
                        "running": running,
                        "completed": list(completed),
                        "decision_rationale": f"MLFQ priority boost: moved {len(moved)} processes to Q0",
                        "state_snapshot": self._get_mlfq_state(procs, q0, q1, q2, running, completed, current_time)
                    }
                last_boost = current_time

            # Arrivals
            while unvisited and unvisited[0]["arrival_time"] <= current_time:
                p = unvisited.pop(0)
                q0.append(p["pid"])
                proc_queue_level[p["pid"]] = 0
                yield {
                    "time": current_time,
                    "event": "PROCESS_ARRIVED",
                    "pid": p["pid"],
                    "process": p,
                    "ready_queue": q0 + q1 + q2,
                    "running": running,
                    "completed": list(completed),
                    "decision_rationale": f"Process P{p['pid']} entered Q0",
                    "state_snapshot": self._get_mlfq_state(procs, q0, q1, q2, running, completed, current_time)
                }

            # Select from highest non-empty queue
            if not running:
                if q0:
                    pid = q0.pop(0)
                    running = pid
                    quantum_remaining = q0_quantum
                    target_queue = "Q0"
                elif q1:
                    pid = q1.pop(0)
                    running = pid
                    quantum_remaining = q1_quantum
                    target_queue = "Q1"
                elif q2:
                    pid = q2.pop(0)
                    running = pid
                    quantum_remaining = rem_time[pid]
                    target_queue = "Q2"
                else:
                    pid = None

                if pid:
                    p = next(pr for pr in procs if pr["pid"] == pid)
                    yield {
                        "time": current_time,
                        "event": "PROCESS_STARTED",
                        "pid": pid,
                        "process": p,
                        "queue_level": proc_queue_level[pid],
                        "ready_queue": q0 + q1 + q2,
                        "running": running,
                        "completed": list(completed),
                        "decision_rationale": f"MLFQ selected P{pid} from {target_queue}",
                        "state_snapshot": self._get_mlfq_state(procs, q0, q1, q2, running, completed, current_time)
                    }

            # Idle
            if not running and not q0 and not q1 and not q2 and unvisited:
                current_time = unvisited[0]["arrival_time"]
                continue

            # Execute
            if running:
                exec_time = min(rem_time[running], quantum_remaining, 1)
                rem_time[running] -= exec_time
                quantum_remaining -= exec_time
                current_time += exec_time

                # Completed
                if rem_time[running] == 0:
                    completed.append(running)
                    yield {
                        "time": current_time,
                        "event": "PROCESS_COMPLETED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "ready_queue": q0 + q1 + q2,
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} completed",
                        "state_snapshot": self._get_mlfq_state(procs, q0, q1, q2, None, completed, current_time)
                    }
                    running = None
                # Quantum expired - demote
                elif quantum_remaining == 0:
                    current_level = proc_queue_level[running]
                    if current_level == 0:
                        q1.append(running)
                        proc_queue_level[running] = 1
                        new_queue = "Q1"
                    elif current_level == 1:
                        q2.append(running)
                        proc_queue_level[running] = 2
                        new_queue = "Q2"
                    else:
                        q2.append(running)
                        new_queue = "Q2"

                    yield {
                        "time": current_time,
                        "event": "QUEUE_CHANGED",
                        "pid": running,
                        "process": next(p for p in procs if p["pid"] == running),
                        "old_queue": f"Q{current_level}",
                        "new_queue": new_queue,
                        "ready_queue": q0 + q1 + q2,
                        "running": None,
                        "completed": list(completed),
                        "decision_rationale": f"P{running} demoted from Q{current_level} to {new_queue}",
                        "state_snapshot": self._get_mlfq_state(procs, q0, q1, q2, None, completed, current_time)
                    }
                    running = None

        self.makespan = current_time

    def _get_state_snapshot(
        self,
        all_procs: List[Dict],
        ready_queue: List[int],
        running: int,
        completed: List[int],
        time: float
    ) -> Dict:
        """Generate complete state snapshot for frontend."""
        return {
            "time": time,
            "ready_queue": [
                {
                    "pid": pid,
                    "name": next(p.get("name", f"P{pid}") for p in all_procs if p["pid"] == pid),
                    "priority": next((p.get("priority", 0) for p in all_procs if p["pid"] == pid), 0)
                }
                for pid in ready_queue
            ],
            "running_process": {
                "pid": running,
                "name": next((p.get("name", f"P{running}") for p in all_procs if p["pid"] == running), None)
            } if running else None,
            "completed_pids": list(completed),
            "makespan": time
        }

    def _get_mlfq_state(
        self,
        all_procs: List[Dict],
        q0: List[int],
        q1: List[int],
        q2: List[int],
        running: int,
        completed: List[int],
        time: float
    ) -> Dict:
        """MLFQ-specific state snapshot."""
        return {
            "time": time,
            "q0": list(q0),
            "q1": list(q1),
            "q2": list(q2),
            "running_process": {
                "pid": running,
                "name": next((p.get("name", f"P{running}") for p in all_procs if p["pid"] == running), None)
            } if running else None,
            "completed_pids": list(completed),
            "makespan": time
        }
