# SysPilot: Project Implementation & Requirement Tracking Ledger

> **Course**: Operating Systems (Sem-1, 3rd Year VIT)  
> **Platform**: SysPilot - Intelligent Linux Process, Resource Management and Scheduling Optimization Platform  
> **Status**: Completed & Verified (18/18 Unit Tests Passed, 8/8 Live APIs Verified)  
> **Last Updated**: 2026-09-16

---

## Master Objective Tracking Matrix

| Objective ID | Requirement Description | Sub-components Implemented | Implementation Status | Verification Results |
|:---:|---|---|:---:|---|
| **OBJ-1** | **Monitor and visualize Linux processes in real time** | - Direct `/proc` filesystem parser (`/proc/stat`, `/proc/meminfo`, `/proc/loadavg`, `/proc/[pid]/stat`, `/proc/[pid]/status`)<br>- Searchable, sortable process table with CPU%, RAM%, RSS, User, State<br>- Process Tree hierarchy (parent-child graph `PPID -> PID`)<br>- Cross-platform OS fallback engine via `psutil` | ✅ **Completed** | Verified live via `/ws/telemetry`, `/api/processes`, `/api/processes/tree`, unit tests in `tests/test_ml_and_proc.py` |
| **OBJ-2** | **Analyze CPU scheduling algorithms & intelligent recommender** | - 7 Algorithms: FCFS, SJF (Non-preemptive), SRTF (Preemptive), Priority (Non-preemptive), Priority (Preemptive with Aging), Round Robin (configurable $\Delta t$), MLFQ (3 queues with aging/boost)<br>- Metrics engine: Turnaround Time ($TAT$), Waiting Time ($WT$), Response Time ($RT$), CPU Utilization, Context Switches<br>- Interactive discrete Gantt timeline visualizer<br>- Workload-driven AI Recommender analyzing burst variance ($CV$), arrival skew, and urgency | ✅ **Completed** | 100% textbook verification tests passed (`tests/test_scheduler.py`), Gantt chart rendering verified |
| **OBJ-3** | **Manage system resources (CPU, Memory, Processes)** | - POSIX signal dispatch: `SIGTERM` (15), `SIGKILL` (9), `SIGSTOP` (19), `SIGCONT` (18)<br>- Dynamic `renice` priority shifting (-20 to 19)<br>- Zombie and Orphan process detector with auto-alerting<br>- Per-core CPU utilization heatmap and virtual memory breakdown | ✅ **Completed** | Verified via signal and renice endpoints, zombie scanner verified |
| **OBJ-4** | **Demonstrate concurrent programming using threads and IPC** | - Bounded Buffer Producer-Consumer using Python Semaphores (`empty`, `full`) and `mutex` Lock<br>- Readers-Writers synchronization with writer starvation avoidance<br>- Dijkstra's Banker's Algorithm for Deadlock Avoidance (Need matrix, Safety algorithm, Safe Sequence $\langle P_i \to \dots \rangle$, and Resource-Request evaluation)<br>- IPC Benchmark comparing Shared Memory vs Message Queue vs OS Pipe | ✅ **Completed** | Multi-threaded race condition tests passed, Banker's safe sequence tests passed (`tests/test_bankers.py`) |
| **OBJ-5** | **Implement a multi-client concurrent file service** | - Multi-client concurrent file server<br>- Thread-safe fine-grained Reader-Writer lock (`RWLock`) per file with writer preference<br>- Simulated OS Page Cache with **LRU (Least Recently Used)** eviction policy and dirty-page flushing<br>- Automated multi-client concurrent traffic stress test harness | ✅ **Completed** | Verified 20+ concurrent operations with 92.24 ops/sec throughput without data corruption (`tests/test_concurrency_and_files.py`) |
| **OBJ-6** | **Predict resource usage using Machine Learning** | - Rolling telemetry ring buffer (120 seconds historical window)<br>- Time-series Ridge Polynomial Regression forecaster for +10s, +30s, +60s horizons<br>- Memory leak detector analyzing monotonic $\Delta RSS / \Delta t > 0$ to prevent OOM Killer<br>- Runaway CPU loop spike detector<br>- Synthetic anomaly injection harness for live demos | ✅ **Completed** | Regression fit and anomaly alarms verified (`tests/test_ml_and_proc.py`) |
| **OBJ-7** | **Provide an interactive dashboard for system analytics** | - Glassmorphic dark-themed single-page web dashboard (`frontend/`)<br>- Real-time WebSocket connection (`/ws/telemetry`) with automatic reconnection<br>- 5 full modular tabs: System Monitor, CPU Scheduler Studio, Concurrency Lab, Concurrent File Hub, ML Analytics<br>- Interactive modals for Process Tree, Signals, and raw `/proc` view | ✅ **Completed** | Full web application verified on `http://127.0.0.1:8000` |

---

## 🧮 Theoretical OS Concepts & Mathematical Formulations

1. **Turnaround Time ($TAT$)**:
   $$TAT_i = C_i - A_i$$
2. **Waiting Time ($WT$)**:
   $$WT_i = TAT_i - B_i$$
3. **Response Time ($RT$)**:
   $$RT_i = \text{FirstExecution}_i - A_i$$
4. **CPU Utilization**:
   $$\text{Utilization} = \frac{\sum B_i}{\text{Total Makespan}} \times 100\%$$
5. **Coefficient of Variation ($CV$) for Scheduling Recommender**:
   $$CV = \frac{\sigma_B}{\mu_B} = \frac{\sqrt{\frac{1}{n}\sum_{i=1}^n (B_i - \mu_B)^2}}{\mu_B}$$
   *If $CV > 0.6$, SRTF is recommended as it minimizes average waiting time mathematically by the SJF Optimality Theorem.*
6. **Banker's Algorithm Safety Condition**:
   $$\text{Need}[i][j] = \text{Max}[i][j] - \text{Allocation}[i][j] \le \text{Work}[j]$$
7. **LRU Page Replacement Policy**:
   $$O(1) \text{ access and eviction using an internal Doubly Linked List + Hash Map (OrderedDict)}$$
8. **Memory Leak Growth Rate**:
   $$\frac{d(RSS)}{dt} = \frac{\text{Cov}(t, RSS)}{\text{Var}(t)} > 0.5 \text{ MB/s} \quad \text{with } R^2 > 0.85$$

---

## 📂 Verification & Test Execution Summary

- **Automated Unit Tests**: 18 passed in 25.84s (`pytest tests/ -v`).
- **Live HTTP & WebSocket Endpoints**: All 8 core subsystem endpoints verified operational.
- **Server Deployment**: Running locally on `http://127.0.0.1:8000` with Swagger UI at `http://127.0.0.1:8000/docs`.
