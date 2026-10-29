"""Dijkstra's Banker's Algorithm for Deadlock Avoidance and Resource Allocation.

Core OS Principles:
- System state is SAFE if there exists at least one sequence <P0, P1, ..., Pn-1>
  of processes such that for each Pi, the resources that Pi can still request
  can be satisfied by the currently available resources plus the resources
  already held by all preceding processes.
- Need Matrix: Need[i][j] = Max[i][j] - Allocation[i][j]
- Safety Algorithm:
    1. Let Work = Available, Finish[i] = False for all i.
    2. Find an index i such that:
       a. Finish[i] == False
       b. Need[i] <= Work
       If no such i exists, go to step 4.
    3. Work = Work + Allocation[i], Finish[i] = True, append Pi to Safe Sequence. Go to step 2.
    4. If Finish[i] == True for all i, system is SAFE. Else, UNSAFE (Deadlock risk).
"""

from typing import List, Dict, Any, Tuple

class BankersAlgorithm:
    """Implements Deadlock Avoidance and Safety checks."""

    @staticmethod
    def calculate_need(allocation: List[List[int]], max_matrix: List[List[int]]) -> List[List[int]]:
        """Compute Need[i][j] = Max[i][j] - Allocation[i][j]."""
        need = []
        for i in range(len(allocation)):
            row = []
            for j in range(len(allocation[i])):
                val = max_matrix[i][j] - allocation[i][j]
                if val < 0:
                    raise ValueError(f"Process P{i} allocation exceeds max claim for resource R{j}")
                row.append(val)
            need.append(row)
        return need

    @staticmethod
    def is_safe_state(
        available: List[int],
        allocation: List[List[int]],
        max_matrix: List[List[int]]
    ) -> Dict[str, Any]:
        """Run the Banker's Safety Algorithm."""
        n = len(allocation) # Process count
        if n == 0:
            return {"is_safe": True, "safe_sequence": [], "steps": [], "need": []}
        m = len(available)  # Resource types count

        need = BankersAlgorithm.calculate_need(allocation, max_matrix)
        work = list(available)
        finish = [False] * n
        safe_sequence = []
        steps = []

        count = 0
        while count < n:
            found = False
            for i in range(n):
                if not finish[i]:
                    # Check if Need[i] <= Work
                    can_allocate = True
                    for j in range(m):
                        if need[i][j] > work[j]:
                            can_allocate = False
                            break

                    if can_allocate:
                        before_work = list(work)
                        # Process Pi completes and releases all allocated resources
                        for j in range(m):
                            work[j] += allocation[i][j]
                        finish[i] = True
                        safe_sequence.append(f"P{i}")
                        found = True
                        count += 1
                        steps.append({
                            "step": count,
                            "process": f"P{i}",
                            "need": need[i],
                            "work_before": before_work,
                            "allocation": allocation[i],
                            "work_after": list(work),
                            "action": f"P{i} satisfied! Released resources {allocation[i]} -> New available: {work}"
                        })
                        break

            if not found:
                # System is in an unsafe state
                deadlocked_processes = [f"P{i}" for i in range(n) if not finish[i]]
                return {
                    "is_safe": False,
                    "safe_sequence": [],
                    "safe_sequence_str": "",
                    "steps": steps,
                    "need": need,
                    "deadlocked_processes": deadlocked_processes,
                    "work_at_failure": work,
                    "message": f"Unsafe state detected! The system cannot guarantee safe execution. Potential deadlock among processes: {', '.join(deadlocked_processes)}"
                }

        return {
            "is_safe": True,
            "safe_sequence": safe_sequence,
            "safe_sequence_str": " -> ".join(safe_sequence),
            "steps": steps,
            "need": need,
            "final_work": work,
            "message": f"System is in a SAFE state. Execution sequence: {' -> '.join(safe_sequence)}"
        }

    @staticmethod
    def request_resources(
        pid: int,
        request: List[int],
        available: List[int],
        allocation: List[List[int]],
        max_matrix: List[List[int]]
    ) -> Dict[str, Any]:
        """Evaluate a dynamic resource request from process Pi."""
        n = len(allocation)
        m = len(available)
        need = BankersAlgorithm.calculate_need(allocation, max_matrix)

        # Condition 1: Request <= Need
        for j in range(m):
            if request[j] > need[pid][j]:
                return {
                    "granted": False,
                    "reason": f"Error: Process P{pid} requested {request[j]} units of R{j}, exceeding its declared maximum need {need[pid][j]}."
                }

        # Condition 2: Request <= Available
        for j in range(m):
            if request[j] > available[j]:
                return {
                    "granted": False,
                    "reason": f"Wait: Process P{pid} must wait. Requested {request[j]} units of R{j}, but only {available[j]} are currently available."
                }

        # Tentatively allocate resources
        trial_available = [available[j] - request[j] for j in range(m)]
        trial_allocation = [list(row) for row in allocation]
        for j in range(m):
            trial_allocation[pid][j] += request[j]

        # Run safety check on tentative state
        safety_check = BankersAlgorithm.is_safe_state(trial_available, trial_allocation, max_matrix)
        if safety_check["is_safe"]:
            return {
                "granted": True,
                "reason": f"Request GRANTED! Tentative state is SAFE. Safe Sequence: {safety_check['safe_sequence_str']}.",
                "safety_check": safety_check,
                "new_available": trial_available,
                "new_allocation": trial_allocation
            }
        else:
            return {
                "granted": False,
                "reason": f"Request DENIED! Granting this request would lead the system into an UNSAFE state (Deadlock risk).",
                "safety_check": safety_check
            }
