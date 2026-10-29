"""CPU Scheduling Algorithms Implementation.

Includes:
1. First-Come, First-Served (FCFS)
2. Shortest Job First (SJF - Non-preemptive)
3. Shortest Remaining Time First (SRTF - Preemptive SJF)
4. Priority Scheduling (Non-preemptive)
5. Priority Scheduling (Preemptive with Aging to prevent starvation)
6. Round Robin (RR - configurable quantum)
7. Multi-Level Feedback Queue (MLFQ - 3 priority tiers with aging/boost)
"""

from typing import List, Dict, Any
from copy import deepcopy

def fcfs(processes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """First-Come, First-Served Scheduling."""
    procs = sorted(deepcopy(processes), key=lambda x: (x["arrival_time"], x["pid"]))
    timeline = []
    current_time = 0

    for p in procs:
        arr = p["arrival_time"]
        burst = p["burst_time"]
        if current_time < arr:
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": arr})
            current_time = arr
        
        timeline.append({"pid": p["pid"], "name": p.get("name", f"P{p['pid']}"), "start": current_time, "end": current_time + burst})
        current_time += burst

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def sjf_non_preemptive(processes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Shortest Job First (Non-preemptive)."""
    procs = deepcopy(processes)
    completed = 0
    n = len(procs)
    current_time = 0
    timeline = []
    is_completed = [False] * n

    while completed < n:
        # Find arrived processes
        available = [
            (i, procs[i]) for i in range(n)
            if not is_completed[i] and procs[i]["arrival_time"] <= current_time
        ]

        if not available:
            # Advance to next arrival
            next_arrival = min([procs[i]["arrival_time"] for i in range(n) if not is_completed[i]])
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_arrival})
            current_time = next_arrival
            continue

        # Pick shortest burst time
        available.sort(key=lambda x: (x[1]["burst_time"], x[1]["arrival_time"], x[1]["pid"]))
        idx, chosen = available[0]

        start = current_time
        end = current_time + chosen["burst_time"]
        timeline.append({"pid": chosen["pid"], "name": chosen.get("name", f"P{chosen['pid']}"), "start": start, "end": end})
        current_time = end
        is_completed[idx] = True
        completed += 1

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def srtf_preemptive(processes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Shortest Remaining Time First (Preemptive SJF)."""
    procs = deepcopy(processes)
    n = len(procs)
    rem_time = [p["burst_time"] for p in procs]
    current_time = 0
    completed = 0
    timeline = []
    last_pid = None

    while completed < n:
        available = [
            i for i in range(n)
            if procs[i]["arrival_time"] <= current_time and rem_time[i] > 0
        ]

        if not available:
            next_arr = min([procs[i]["arrival_time"] for i in range(n) if rem_time[i] > 0])
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_arr})
            current_time = next_arr
            continue

        # Choose minimum remaining time
        chosen_idx = min(available, key=lambda i: (rem_time[i], procs[i]["arrival_time"], procs[i]["pid"]))
        p = procs[chosen_idx]

        timeline.append({"pid": p["pid"], "name": p.get("name", f"P{p['pid']}"), "start": current_time, "end": current_time + 1})
        rem_time[chosen_idx] -= 1
        current_time += 1

        if rem_time[chosen_idx] == 0:
            completed += 1

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def priority_non_preemptive(processes: List[Dict[str, Any]], lower_is_higher: bool = True) -> Dict[str, Any]:
    """Priority Scheduling (Non-preemptive)."""
    procs = deepcopy(processes)
    n = len(procs)
    completed = 0
    current_time = 0
    timeline = []
    is_completed = [False] * n

    while completed < n:
        available = [
            (i, procs[i]) for i in range(n)
            if not is_completed[i] and procs[i]["arrival_time"] <= current_time
        ]

        if not available:
            next_arr = min([procs[i]["arrival_time"] for i in range(n) if not is_completed[i]])
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_arr})
            current_time = next_arr
            continue

        # Sort by priority
        sign = 1 if lower_is_higher else -1
        available.sort(key=lambda x: (sign * x[1].get("priority", 0), x[1]["arrival_time"], x[1]["pid"]))
        idx, chosen = available[0]

        start = current_time
        end = current_time + chosen["burst_time"]
        timeline.append({"pid": chosen["pid"], "name": chosen.get("name", f"P{chosen['pid']}"), "start": start, "end": end})
        current_time = end
        is_completed[idx] = True
        completed += 1

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def priority_preemptive_aging(processes: List[Dict[str, Any]], aging_rate: int = 1, lower_is_higher: bool = True) -> Dict[str, Any]:
    """Priority Scheduling (Preemptive with Aging to prevent starvation)."""
    procs = deepcopy(processes)
    n = len(procs)
    rem_time = [p["burst_time"] for p in procs]
    dynamic_priority = [p.get("priority", 0) for p in procs]
    waiting_steps = [0] * n
    current_time = 0
    completed = 0
    timeline = []

    while completed < n:
        available = [
            i for i in range(n)
            if procs[i]["arrival_time"] <= current_time and rem_time[i] > 0
        ]

        if not available:
            next_arr = min([procs[i]["arrival_time"] for i in range(n) if rem_time[i] > 0])
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_arr})
            current_time = next_arr
            continue

        # Apply aging to waiting processes: every 5 time units waiting, bump priority
        for idx in available:
            if waiting_steps[idx] >= 5 and aging_rate > 0:
                if lower_is_higher:
                    dynamic_priority[idx] = max(1, dynamic_priority[idx] - aging_rate)
                else:
                    dynamic_priority[idx] += aging_rate
                waiting_steps[idx] = 0

        # Choose best priority
        sign = 1 if lower_is_higher else -1
        chosen_idx = min(available, key=lambda i: (sign * dynamic_priority[i], procs[i]["arrival_time"], procs[i]["pid"]))
        p = procs[chosen_idx]

        timeline.append({"pid": p["pid"], "name": p.get("name", f"P{p['pid']}"), "start": current_time, "end": current_time + 1})
        rem_time[chosen_idx] -= 1
        current_time += 1

        # Increment waiting counters for others
        for i in available:
            if i != chosen_idx:
                waiting_steps[i] += 1

        if rem_time[chosen_idx] == 0:
            completed += 1

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def round_robin(processes: List[Dict[str, Any]], quantum: int = 2) -> Dict[str, Any]:
    """Round Robin Scheduling with configurable time quantum."""
    procs = deepcopy(processes)
    n = len(procs)
    rem_time = {p["pid"]: p["burst_time"] for p in procs}
    proc_map = {p["pid"]: p for p in procs}
    
    # Sort initial arrivals
    unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))
    ready_queue = []
    timeline = []
    current_time = 0

    # Add first arrived
    while unvisited and unvisited[0]["arrival_time"] <= current_time:
        ready_queue.append(unvisited.pop(0)["pid"])

    if not ready_queue and unvisited:
        first = unvisited.pop(0)
        timeline.append({"pid": "IDLE", "name": "IDLE", "start": 0, "end": first["arrival_time"]})
        current_time = first["arrival_time"]
        ready_queue.append(first["pid"])

    while ready_queue or unvisited:
        if not ready_queue:
            next_p = unvisited.pop(0)
            timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_p["arrival_time"]})
            current_time = next_p["arrival_time"]
            ready_queue.append(next_p["pid"])

        pid = ready_queue.pop(0)
        p = proc_map[pid]
        exec_time = min(rem_time[pid], quantum)

        timeline.append({"pid": pid, "name": p.get("name", f"P{pid}"), "start": current_time, "end": current_time + exec_time})
        current_time += exec_time
        rem_time[pid] -= exec_time

        # Check for new arrivals during execution
        while unvisited and unvisited[0]["arrival_time"] <= current_time:
            ready_queue.append(unvisited.pop(0)["pid"])

        # Re-queue if not finished
        if rem_time[pid] > 0:
            ready_queue.append(pid)

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def mlfq(processes: List[Dict[str, Any]], q0_quantum: int = 2, q1_quantum: int = 4, boost_interval: int = 20) -> Dict[str, Any]:
    """Multi-Level Feedback Queue (3 Tiers with Priority Boost).
    
    Queue 0: Highest priority, RR (quantum = q0_quantum)
    Queue 1: Medium priority, RR (quantum = q1_quantum)
    Queue 2: Lowest priority, FCFS
    """
    procs = deepcopy(processes)
    rem_time = {p["pid"]: p["burst_time"] for p in procs}
    proc_map = {p["pid"]: p for p in procs}
    unvisited = sorted(procs, key=lambda x: (x["arrival_time"], x["pid"]))

    # 3 queues
    q0, q1, q2 = [], [], []
    timeline = []
    current_time = 0
    last_boost = 0

    while unvisited or q0 or q1 or q2:
        # Priority boost to avoid starvation
        if boost_interval > 0 and (current_time - last_boost) >= boost_interval:
            q0.extend(q1)
            q0.extend(q2)
            q1.clear()
            q2.clear()
            last_boost = current_time

        # Add newly arrived processes into Q0
        while unvisited and unvisited[0]["arrival_time"] <= current_time:
            q0.append(unvisited.pop(0)["pid"])

        # If all queues empty, advance time
        if not q0 and not q1 and not q2:
            if unvisited:
                next_p = unvisited.pop(0)
                timeline.append({"pid": "IDLE", "name": "IDLE", "start": current_time, "end": next_p["arrival_time"]})
                current_time = next_p["arrival_time"]
                q0.append(next_p["pid"])
                continue
            else:
                break

        # Select process from highest non-empty queue
        if q0:
            pid = q0.pop(0)
            quantum = q0_quantum
            target_demote = q1
        elif q1:
            pid = q1.pop(0)
            quantum = q1_quantum
            target_demote = q2
        else:
            pid = q2.pop(0)
            quantum = rem_time[pid] # FCFS
            target_demote = q2

        p = proc_map[pid]
        exec_time = min(rem_time[pid], quantum)

        timeline.append({"pid": pid, "name": p.get("name", f"P{pid}"), "start": current_time, "end": current_time + exec_time})
        current_time += exec_time
        rem_time[pid] -= exec_time

        # Catch new arrivals into Q0
        while unvisited and unvisited[0]["arrival_time"] <= current_time:
            q0.append(unvisited.pop(0)["pid"])

        # Demote if still has work
        if rem_time[pid] > 0:
            target_demote.append(pid)

    return {"timeline": _merge_timeline(timeline), "makespan": current_time}


def _merge_timeline(timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge contiguous blocks for the same process."""
    if not timeline:
        return []
    merged = [timeline[0].copy()]
    for block in timeline[1:]:
        last = merged[-1]
        if last["pid"] == block["pid"]:
            last["end"] = block["end"]
        else:
            merged.append(block.copy())
    return merged
