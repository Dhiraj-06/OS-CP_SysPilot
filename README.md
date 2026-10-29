# SysPilot: An Intelligent Linux Process, Resource Management & Scheduling Optimization Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SysPilot** is a unified Operating Systems platform that integrates real-time Linux process management, intelligent CPU scheduling recommendations, concurrent programming & deadlock avoidance, a multi-client concurrent file service, and machine learning-driven resource forecasting into a modern interactive web dashboard.

---

## 🎯 Key Objectives & Implemented Features

### 1. 🖥️ Real-Time Linux Process & Kernel Observability
- **Direct `/proc` Filesystem Parser**: Reads raw kernel pseudo-files (`/proc/stat`, `/proc/meminfo`, `/proc/loadavg`, `/proc/[pid]/stat`, `/proc/[pid]/status`) with automated cross-platform fallback for Windows/macOS.
- **Process Hierarchy Tree**: Reconstructs the complete parent-child process tree ($PPID \rightarrow PID$).
- **Process Signals & Priority**: Send `SIGTERM`, `SIGKILL`, `SIGSTOP`, `SIGCONT`, and adjust scheduling priorities via `renice` (-20 to 19).
- **Zombie & Orphan Detection**: Identifies defunct processes awaiting parent `wait()` or adopted by PID 1 (`init`/`systemd`).

### 2. ⏱️ CPU Scheduling Simulator & Intelligent Recommender
- **7 Algorithms Implemented**:
  1. First-Come First-Served (FCFS)
  2. Shortest Job First (SJF - Non-preemptive)
  3. Shortest Remaining Time First (SRTF - Preemptive SJF)
  4. Priority Scheduling (Non-preemptive)
  5. Priority Scheduling (Preemptive with Aging to prevent starvation)
  6. Round Robin (RR - configurable quantum $\Delta t$)
  7. Multi-Level Feedback Queue (MLFQ - 3 priority tiers with priority boost)
- **Comprehensive Metrics**: Turnaround Time ($TAT$), Waiting Time ($WT$), Response Time ($RT$), CPU Utilization, Throughput, and Context Switch Overhead.
- **Discrete Gantt Execution Timeline**: Interactive timeline showing process blocks, idle gaps, and context switches.
- **Workload-Driven AI Recommender**: Analyzes statistical workload properties (Coefficient of Variation $CV$, arrival distribution, urgency) to recommend the mathematically optimal algorithm with academic trade-off justifications.

### 3. 🔒 Concurrency, Synchronization & Deadlock Sandbox
- **Bounded Buffer (Producer-Consumer)**: Implements semaphore coordination using `empty`, `full`, and `mutex` locks with animated buffer occupancy.
- **Readers-Writers Problem**: Implements shared concurrent reading with exclusive writer mutual exclusion and writer starvation avoidance.
- **Dijkstra's Banker's Algorithm**: Complete Deadlock Avoidance engine computing the Need Matrix ($Need = Max - Allocation$), the Safety Algorithm finding valid Safe Sequences ($\langle P_i \to \dots \rangle$), and dynamic Resource-Request evaluations.
- **IPC Benchmark**: Measures latency ($\mu s$) and throughput ($MB/s$) comparing Shared Memory, Message Queues, and Pipes.

### 4. 📂 Multi-Client Concurrent File Service
- **Thread-Safe Reader-Writer Locking**: Fine-grained per-file RWLock with writer preference.
- **Simulated OS Page Cache (LRU)**: Tracks cache hits, misses, dirty-page status, and automatic flush-on-eviction.
- **Multi-Client Traffic Generator**: Automated stress test harness firing concurrent read/write/append requests across multiple client threads.

### 5. 🧠 Machine Learning Forecasting & Anomaly Center
- **Time-Series Resource Forecasting**: Ridge Polynomial Regression predicting CPU and Memory load for +10s, +30s, and +60s horizons with $R^2$ model confidence metrics.
- **Memory Leak Detection**: Detects processes with monotonic growth ($\frac{d(RSS)}{dt} > 0$) to flag leaks before the Linux OOM Killer is triggered.
- **CPU Spike Detection**: Flags rogue single-threaded infinite loops.
- **Synthetic Anomaly Injection**: Test buttons to simulate memory leaks and CPU spikes live during evaluation.

---

## 🏗️ Architecture & Directory Structure

```
d:/VIT-Third_Year-Sem-1/OS/Course_Project/
├── PROJECT_TRACKING.md                # Living status ledger tracking all 7 objectives
├── README.md                          # Project documentation and submission guide
├── requirements.txt                   # Project dependencies
├── run.py                             # Unified server launcher
│
├── backend/
│   ├── config.py                      # Global configuration & directories
│   ├── main.py                        # FastAPI server & WebSocket router
│   ├── core/                          # [OBJ 1 & 3] /proc parser, process manager, metrics
│   ├── scheduler/                     # [OBJ 2] 7 Scheduling algorithms, simulator, recommender
│   ├── concurrency/                   # [OBJ 4] Banker's algorithm, Producer-Consumer, IPC
│   ├── file_service/                  # [OBJ 5] Multi-client server, RWLock, LRU page cache
│   └── ml/                            # [OBJ 6] Time-series forecaster & anomaly detector
│
├── frontend/                          # [OBJ 7] Interactive Glassmorphic Web Dashboard
│   ├── index.html                     # Single-page shell
│   ├── css/styles.css                 # Dark-mode glassmorphic theme
│   └── js/                            # Modular JavaScript controllers
│
└── tests/                             # Automated test suite
    ├── test_scheduler.py              # Scheduling algorithms & metrics tests
    ├── test_bankers.py                # Banker's algorithm safe/unsafe tests
    ├── test_concurrency_and_files.py  # Concurrency, RWLock, and LRU cache tests
    ├── test_ml_and_proc.py            # /proc parser and ML forecaster tests
    └── verify_endpoints.py            # End-to-end API integration tests
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Launch SysPilot Platform
```powershell
python run.py
```
Open your browser and navigate to:
- **Interactive Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Live WebSocket Telemetry**: `ws://127.0.0.1:8000/ws/telemetry`

---

## 🧪 Running Automated Tests

Run the complete test suite via `pytest`:
```powershell
python -m pytest tests/ -v
```
*(All 18 unit tests cover scheduling, Banker's algorithm, synchronization, LRU caching, `/proc` parsing, and ML forecasting).*

To verify all live API endpoints:
```powershell
python tests/verify_endpoints.py
```

---

## 💡 Viva & Presentation Tips for Evaluators

1. **How `/proc` works**: Explain that `/proc` is not a physical disk filesystem, but a virtual window provided by the Linux kernel. Show [backend/core/proc_parser.py](file:///d:/VIT-Third_Year-Sem-1/OS/Course_Project/backend/core/proc_parser.py) which reads `/proc/stat` for CPU ticks and `/proc/meminfo` for memory breakdown.
2. **Scheduling Optimality**: When asked why SRTF is optimal, explain that according to the Shortest Job First optimality theorem, scheduling the shortest remaining burst time mathematically minimizes the sum of waiting times $\sum WT_i$.
3. **Preventing Starvation**: Show the **Aging mechanism** implemented in `priority_preemptive_aging` and the **Priority Boost interval** in `mlfq` which periodically promotes lower-tier jobs to higher-priority queues.
4. **Banker's Algorithm Need Matrix**: Explain the formula $Need[i][j] = Max[i][j] - Allocation[i][j]$, and demonstrate the step-by-step release of resources in the Safe Sequence visualizer.
5. **Reader-Writer Fair Locking**: Explain how writer starvation is prevented using `_waiting_writers` counter in `rw_lock.py`.
6. **LRU Page Cache**: Explain the $O(1)$ lookup and eviction mechanics and dirty-page writeback simulating the OS `pdflush` daemon.
