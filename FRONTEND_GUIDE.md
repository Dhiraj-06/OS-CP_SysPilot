# SysPilot: Complete Frontend Architecture & Customization Guide

This document is your blueprint for understanding, modifying, and redesigning the frontend of SysPilot. When you make changes or want to overhaul the UI, you can follow this specification so the frontend will connect seamlessly with the FastAPI backend without any broken links.

---

## 1. Frontend File Architecture

All frontend code resides in the `frontend/` directory and contains zero complex build setups (no Node.js build steps, no Webpack/Vite bundlers required). It runs directly as pure, modern ES6+ JavaScript, CSS3, and HTML5.

```
frontend/
├── index.html               # Main single-page HTML layout & structural containers
├── css/
│   └── styles.css           # Design system: tokens, dark-mode colors, glassmorphism, responsive grid
└── js/
    ├── app.js               # Core app controller, tab switcher, modal manager, toast notifications
    ├── websocket.js         # Real-time WebSocket manager with automatic reconnection & dispatch
    ├── process_view.js      # System Monitor: per-core heatmap, process table, signals, process tree modal
    ├── scheduler_view.js    # CPU Scheduler: process editor, Gantt chart renderer, AI recommendation card
    ├── concurrency_view.js  # Deadlock & Sync: Banker's algorithm matrices, Bounded Buffer, Readers-Writers, IPC
    ├── file_service_view.js # File Hub: LRU cache table, concurrent client console, stress test runner
    └── ml_view.js           # ML Analytics: +10s/+30s/+60s forecast cards, memory leak alerts, test simulators
```

---

## 2. CSS Design System & Theme Tokens

All styling is managed through CSS custom properties (variables) defined at the top of [frontend/css/styles.css](file:///d:/VIT-Third_Year-Sem-1/OS/Course_Project/frontend/css/styles.css#L4-L35).

### Color Palette Tokens
| Variable | Default Hex | Purpose / Description |
|---|---|---|
| `--bg-primary` | `#0a0e17` | Root background color (deep space blue-black) |
| `--bg-secondary` | `#111827` | Modal bodies and dropdown background |
| `--bg-card` | `rgba(18, 26, 43, 0.75)` | Semi-transparent card background for glassmorphism |
| `--border-color` | `rgba(255, 255, 255, 0.08)` | Subtle card borders |
| `--border-glow` | `rgba(0, 242, 254, 0.25)` | Glowing borders for active or alert components |
| `--text-primary` | `#f3f4f6` | High-contrast body text |
| `--text-secondary` | `#9ca3af` | Muted subtitles and secondary labels |
| `--accent-cyan` | `#00f2fe` | Primary highlight (CPU, safe sequences, links) |
| `--accent-blue` | `#4facfe` | Secondary highlight (Disk, mid-term forecasts) |
| `--accent-emerald`| `#00e676` | Success status, active processes, shared memory |
| `--accent-amber` | `#ffab00` | Warnings, context switches, disk storage |
| `--accent-rose` | `#ff1744` | Errors, memory leaks, SIGKILL, unsafe deadlocks |
| `--accent-purple`| `#b388ff` | Turnaround time, RAM forecasts, consumers |

### How to Change the Theme
To switch to another look (e.g. Cyberpunk Neon, Minimalist Monochrome, or Light Mode), simply modify the `:root` block in `frontend/css/styles.css`. All cards, charts, and progress bars inherit these variables automatically.

---

## 3. DOM Element Contract (Required Element IDs)

If you modify or rewrite `frontend/index.html`, **keep the following Element IDs intact** so the JavaScript controllers can bind to them:

### A. Navigation & Telemetry Quickbar
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `btn-tab-monitor` | `<button data-tab="tab-monitor">` | Switches to System Monitor |
| `btn-tab-scheduler`| `<button data-tab="tab-scheduler">` | Switches to CPU Scheduler Studio |
| `btn-tab-concurrency`| `<button data-tab="tab-concurrency">` | Switches to Concurrency & Deadlock Lab |
| `btn-tab-files` | `<button data-tab="tab-files">` | Switches to Concurrent File Hub |
| `btn-tab-ml` | `<button data-tab="tab-ml">` | Switches to ML Analytics |
| `ws-indicator` | `<div>` or `<span>` | Status dot (class `offline` added on disconnect) |
| `ws-status-text` | `<span>` | Text showing "Live Telemetry Active" or "Offline" |
| `hdr-uptime` | `<span>` | System uptime string (e.g., "2h 15m 4s") |
| `quick-cpu-val` | `<span>` | Aggregate CPU % (e.g., "34.2") |
| `quick-cpu-bar` | `<div>` | Progress bar filled via `style.width = "%"` |
| `quick-mem-val` | `<span>` | Memory % (e.g., "58.1") |
| `quick-mem-bar` | `<div>` | Progress bar for memory usage |
| `quick-disk-val`| `<span>` | Disk I/O throughput in KB/s |
| `quick-net-val` | `<span>` | Network throughput in KB/s |

### B. System Monitor Tab (`#tab-monitor`)
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `cpu-core-grid` | `<div>` | Container where per-core CPU heatmap cells are rendered |
| `process-table-body` | `<tbody>` | Rows for running processes (`PID`, `PPID`, `Name`, `CPU%`, etc.) |
| `proc-search-input`| `<input type="text">` | Search bar filtering by PID or Process Name |
| `proc-sort-select` | `<select>` | Sort dropdown (`cpu_percent`, `memory_percent`, `pid`, `name`) |
| `btn-refresh-procs`| `<button>` | Triggers manual process table re-fetch |
| `btn-open-tree` | `<button>` | Opens the process tree modal (`#modal-process-tree`) |
| `btn-scan-zombies` | `<button>` | Runs the zombie & orphan detector |

### C. CPU Scheduler Tab (`#tab-scheduler`)
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `workload-preset-select` | `<select>` | Pre-fills workload table (`standard`, `high_variance`, etc.) |
| `btn-add-proc-row` | `<button>` | Appends a new editable process row |
| `scheduler-proc-rows` | `<tbody>` | Container for editable process inputs |
| `selected-algorithm` | `<select>` | Algorithm selector (`fcfs`, `sjf`, `srtf`, `round_robin`, etc.) |
| `quantum-input` | `<input type="number">` | Time quantum $\Delta t$ for Round Robin / MLFQ |
| `mlfq-boost-input` | `<input type="number">` | Priority boost interval for MLFQ |
| `btn-run-simulation` | `<button>` | Runs discrete-event simulation |
| `btn-compare-all` | `<button>` | Compares all 7 algorithms simultaneously |
| `btn-ai-recommend` | `<button>` | Analyzes workload and produces recommendation |
| `gantt-timeline-bar` | `<div>` | Flexible container where timeline blocks are drawn |
| `gantt-ticks-bar` | `<div>` | Timestamp marks ($0, 2, 5, \dots$) below the Gantt chart |
| `scheduler-results-body` | `<tbody>` | Table showing computed $CT, TAT, WT, RT$ per process |
| `rec-algo-title` | `<h3>` | Displays the recommended algorithm name |
| `rec-avg-wt` | `<div>` | Recommended algorithm's Average Waiting Time |
| `rec-justification-list` | `<div>` | List of AI explanations and trade-offs |

### D. Concurrency & Deadlock Tab (`#tab-concurrency`)
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `bankers-available-inputs` | Container with 3 `<input>` | Available resource instances $[R_0, R_1, R_2]$ |
| `bankers-alloc-table` | `<tbody>` | $5 \times 3$ Allocation Matrix inputs |
| `bankers-max-table` | `<tbody>` | $5 \times 3$ Maximum Claim Matrix inputs |
| `btn-run-bankers` | `<button>` | Triggers Banker's safety check |
| `bankers-sequence-text` | `<div>` | Displays safe sequence ($\langle P_1 \to P_3 \to \dots \rangle$) or deadlock alert |
| `btn-run-producer-consumer` | `<button>` | Runs Bounded Buffer synchronization test |
| `buffer-slot-display` | `<div>` | Container showing the 6 buffer slots |
| `btn-run-rw-test` | `<button>` | Runs Readers-Writers synchronization test |
| `rw-active-readers` | `<div>` | Live active readers counter |
| `rw-active-writers` | `<div>` | Live active writers status |
| `btn-run-ipc-bench` | `<button>` | Executes Shared Memory vs Pipe vs Queue benchmark |

### E. Concurrent File Hub Tab (`#tab-files`)
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `cache-hit-ratio-badge` | `<span>` | LRU Page Cache Hit Ratio percentage |
| `cached-pages-body` | `<tbody>` | Table of files currently held in LRU memory cache |
| `btn-launch-stress-test` | `<button>` | Fires concurrent multi-client thread traffic |
| `file-activity-body` | `<tbody>` | Live stream of client `READ`, `WRITE`, `APPEND` requests |
| `manual-client-id` | `<input>` | Client name for manual testing |
| `manual-filename` | `<input>` | Target filename |
| `manual-file-content` | `<textarea>` | File payload content |
| `btn-manual-read` | `<button>` | Performs thread-safe shared read |
| `btn-manual-write` | `<button>` | Performs thread-safe exclusive write |

### F. ML Analytics Tab (`#tab-ml`)
| Element ID | Expected HTML Element | Purpose |
|---|---|---|
| `forecast-cpu-10` | `<div>` | CPU forecast for $+10\text{s}$ |
| `forecast-mem-10` | `<div>` | RAM forecast for $+10\text{s}$ |
| `forecast-cpu-30` | `<div>` | CPU forecast for $+30\text{s}$ |
| `forecast-cpu-60` | `<div>` | CPU forecast for $+60\text{s}$ |
| `anomaly-status-badge`| `<span>` | "NORMAL" or "ANOMALY DETECTED" |
| `anomaly-alerts-container` | `<div>` | Memory leak warning cards ($\Delta RSS / \Delta t > 0$) |
| `btn-sim-leak` | `<button>` | Injects a synthetic memory leak for live demo |
| `btn-sim-cpu-hog` | `<button>` | Injects a synthetic CPU spike for live demo |

---

## 4. Backend Communication Protocols

### A. Real-Time WebSocket Telemetry
- **Endpoint**: `ws://127.0.0.1:8000/ws/telemetry`
- **Direction**: Server $\to$ Client broadcast every $1.0\text{ second}$.
- **Payload Structure**:
```json
{
  "type": "telemetry_tick",
  "system": {
    "timestamp": 1726470000.12,
    "cpu": { "aggregate_percent": 34.2, "per_core_percent": [25.0, 40.5, 12.0, 60.0], "logical_cores": 4 },
    "memory": { "total": 17179869184, "used": 8589934592, "percent": 50.0, "cached": 2147483648, "swap_percent": 0.0 },
    "disk": { "percent": 65.0, "read_kb_s": 120.5, "write_kb_s": 45.0 },
    "network": { "rx_kb_s": 32.0, "tx_kb_s": 14.5 },
    "system": { "uptime_formatted": "3h 12m 45s", "total_processes": 142, "load": { "load1": 1.45, "load5": 1.20, "load15": 1.10 } }
  },
  "forecast": {
    "current_cpu": 34.2,
    "current_mem": 50.0,
    "cpu_trend": "Stable",
    "mem_trend": "Increasing",
    "predictions": [
      { "horizon_seconds": 10, "predicted_cpu_percent": 36.0, "predicted_mem_percent": 51.2, "cpu_delta": 1.8, "mem_delta": 1.2 },
      { "horizon_seconds": 30, "predicted_cpu_percent": 38.5, "predicted_mem_percent": 52.8, "cpu_delta": 4.3, "mem_delta": 2.8 },
      { "horizon_seconds": 60, "predicted_cpu_percent": 42.0, "predicted_mem_percent": 55.0, "cpu_delta": 7.8, "mem_delta": 5.0 }
    ],
    "confidence_r2": { "cpu": 0.92, "mem": 0.88 }
  },
  "anomalies": {
    "status": "NORMAL",
    "total_anomalies": 0,
    "memory_leaks": [],
    "cpu_hogs": []
  }
}
```

### B. Key REST Endpoints & Payloads

1. **Simulate Scheduling**:
   - `POST /api/scheduler/simulate`
   - Body:
     ```json
     {
       "algorithm": "round_robin",
       "processes": [
         {"pid": 1, "name": "P1", "arrival_time": 0, "burst_time": 5, "priority": 1},
         {"pid": 2, "name": "P2", "arrival_time": 1, "burst_time": 3, "priority": 2}
       ],
       "params": { "quantum": 2 }
     }
     ```

2. **Banker's Safety Check**:
   - `POST /api/concurrency/bankers/safety`
   - Body:
     ```json
     {
       "available": [3, 3, 2],
       "allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
       "max_matrix": [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
     }
     ```

3. **File Service Concurrent Operations**:
   - `POST /api/file_service/read` $\to$ `{ "client_id": "C1", "filename": "test.txt" }`
   - `POST /api/file_service/write` $\to$ `{ "client_id": "C1", "filename": "test.txt", "content": "..." }`
   - `POST /api/file_service/stress_test` $\to$ `{ "num_clients": 6, "operations_per_client": 8 }`

---

## 5. How to Re-Integrate Your Modified Frontend

Whenever you customize the frontend:
1. Simply save your modified HTML, CSS, or JS files directly into the `frontend/` directory.
2. Refresh your web browser at [http://127.0.0.1:8000](http://127.0.0.1:8000) (`Ctrl + F5` to clear browser cache).
3. Because FastAPI serves static files directly from `frontend/`, **no compilation, bundling, or server restarts are required**—your changes will appear immediately!
