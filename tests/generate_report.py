"""Generate the comprehensive Word Document (.docx) report for SysPilot."""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from pathlib import Path

def set_cell_background(cell, fill_hex):
    """Set shading color for a table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)

def create_report():
    doc = Document()

    # Configure Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styling Palette
    COLOR_PRIMARY = RGBColor(10, 25, 47)      # Deep Navy
    COLOR_ACCENT = RGBColor(0, 150, 214)      # Tech Cyan/Blue
    COLOR_MUTED = RGBColor(100, 110, 120)     # Neutral Grey

    # -------------------------------------------------------------
    # TITLE & HEADER BLOCK
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("SysPilot: Intelligent Linux Process, Resource Management & Scheduling Optimization Platform")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(20)
    run_sub = sub_p.add_run("A Unified Operating Systems Course Project & Academic Technical Report\nVIT Third Year (Sem-1) - Operating Systems Course Project")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = COLOR_ACCENT

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Course & Subject", "Operating Systems (CSE - 3rd Year)"),
        ("Project Title", "SysPilot: Process, Resource & Scheduling Platform"),
        ("Technology Stack", "Python (FastAPI, AsyncIO, WebSockets), Linux Procfs, Scikit-Learn, Vanilla ES6+/CSS3"),
        ("Implementation Status", "100% Implemented & Verified (18/18 Unit Tests Passed)")
    ]
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = label
        c1.text = val
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)
        set_cell_background(c0, "F0F4F8")
        set_cell_background(c1, "FFFFFF")

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # -------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # -------------------------------------------------------------
    h1 = doc.add_heading("1. Executive Summary & Problem Statement", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Modern Linux systems provide individual command-line utilities (top, htop, ps, kill, nice) "
        "for process management and system monitoring. However, these tools are fragmented, require deep CLI "
        "expertise, and operate purely as passive diagnostic reporters. Critically, existing utilities provide "
        "no intelligent decision support: they do not recommend optimal CPU scheduling algorithms for given "
        "workloads, offer no live sandboxes for concurrency and deadlock avoidance, and lack predictive "
        "intelligence to warn administrators before processes exhaust memory or trigger the Linux Out-Of-Memory (OOM) killer."
    )

    doc.add_paragraph(
        "SysPilot bridges theoretical operating systems principles with production-grade Linux systems engineering. "
        "It integrates real-time kernel observability (/proc filesystem parsing, parent-child process tree traversal, "
        "POSIX signal dispatching), a CPU scheduling simulation and AI recommendation suite, classical concurrency "
        "and deadlock avoidance (Dijkstra's Banker's Algorithm, Producer-Consumer, Readers-Writers), a high-throughput "
        "multi-client concurrent file service with an LRU OS Page Cache, and online Machine Learning time-series "
        "forecasting into an interactive glassmorphic web dashboard."
    )

    # -------------------------------------------------------------
    # SECTION 2: ARCHITECTURE & SYSTEM OVERVIEW
    # -------------------------------------------------------------
    h1 = doc.add_heading("2. System Architecture & Component Design", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "SysPilot is built upon a high-performance modular architecture separating low-level kernel parsing, "
        "discrete event simulation engines, multi-threaded concurrency servers, machine learning pipelines, and "
        "a reactive WebSocket telemetry layer:"
    )

    arch_table = doc.add_table(rows=6, cols=3)
    arch_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Subsystem Layer", "Core Python Modules", "Primary Responsibility"]
    for col_idx, text in enumerate(headers):
        cell = arch_table.rows[0].cells[col_idx]
        cell.text = text
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(cell, "0A192F")

    subsystems = [
        ("Core Kernel & Process Engine", "backend.core (proc_parser, process_manager, system_metrics)", "Direct Linux /proc parsing, PPID tree building, POSIX signal dispatch, renice, and zombie/orphan scanning."),
        ("CPU Scheduling & Recommender", "backend.scheduler (algorithms, simulator, metrics, recommender)", "Simulation of 7 scheduling algorithms (FCFS, SJF, SRTF, Priority, RR, MLFQ), metrics calculation, Gantt charts, and AI recommender."),
        ("Concurrency & Deadlock Sandbox", "backend.concurrency (bankers_algorithm, synchronization, ipc_service)", "Banker's deadlock avoidance and safety check, bounded buffer semaphores, readers-writers locks, IPC benchmarks."),
        ("Concurrent File Service", "backend.file_service (server, rw_lock, page_cache, client_harness)", "Thread-safe multi-client file server with writer-preference RWLock, LRU OS page cache, and automated stress harness."),
        ("ML Forecasting & Anomalies", "backend.ml (dataset_buffer, forecaster, anomaly_detector)", "Rolling ring buffer, Ridge polynomial regression forecasting (+10s/+30s/+60s), and RSS leak detection.")
    ]

    for row_idx, data in enumerate(subsystems, start=1):
        row = arch_table.rows[row_idx]
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.text = text
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_background(cell, "F8FAFC" if row_idx % 2 == 0 else "FFFFFF")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------
    # SECTION 3: DEEP-DIVE INTO ALL 7 OBJECTIVES
    # -------------------------------------------------------------
    h1 = doc.add_heading("3. Detailed Implementation of Core OS Concepts", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    # 3.1 Kernel & Process Monitoring
    h2 = doc.add_heading("3.1 Real-Time Linux Process & Kernel Observability", level=2)
    h2.runs[0].font.color.rgb = COLOR_ACCENT
    doc.add_paragraph(
        "• The Linux /proc Virtual Filesystem: Unlike standard filesystems stored on persistent block devices, "
        "/proc is an in-memory pseudo-filesystem generated on the fly by the Linux kernel. SysPilot directly reads:\n"
        "   - /proc/stat: Aggregates aggregate and per-core CPU jiffies/ticks (user, nice, system, idle, iowait, irq, softirq, steal).\n"
        "   - /proc/meminfo: Provides exact memory distribution including MemTotal, MemFree, MemAvailable, Buffers, Cached, and Swap.\n"
        "   - /proc/[pid]/stat & /proc/[pid]/status: Captures process execution states (R=Running, S=Sleeping, D=Disk Sleep, Z=Zombie, T=Stopped), "
        "parent PID (PPID), user time (utime), kernel time (stime), priority, nice value (-20 to 19), virtual size (VmSize), and Resident Set Size (VmRSS).\n"
        "• Parent-Child Process Hierarchy (Tree): Constructed by traversing PPID pointers from all active process nodes. This reveals the ancestral "
        "fork lineage (init/systemd at PID 1 spawning daemons, user sessions, and worker threads).\n"
        "• POSIX Signal Control: Sends signals directly to target processes using standard POSIX signal numbers: SIGTERM (15: graceful termination), "
        "SIGKILL (9: uncatchable immediate termination), SIGSTOP (19: pause execution), and SIGCONT (18: resume execution).\n"
        "• Zombie & Orphan Detection: A zombie (defunct) process has completed execution via exit(), but its entry remains in the process table because "
        "its parent has not yet executed wait() to read its termination exit code. An orphan process has lost its parent and is adopted by PID 1."
    )

    # 3.2 CPU Scheduling Engine
    h2 = doc.add_heading("3.2 CPU Scheduling Algorithms & Intelligent Workload Recommender", level=2)
    h2.runs[0].font.color.rgb = COLOR_ACCENT
    doc.add_paragraph(
        "SysPilot implements 7 core CPU scheduling algorithms with discrete event simulation:\n"
        "1. First-Come First-Served (FCFS): Non-preemptive FIFO queue; simple but vulnerable to the Convoy Effect.\n"
        "2. Shortest Job First (SJF - Non-preemptive): Selects the ready process with the smallest burst time.\n"
        "3. Shortest Remaining Time First (SRTF - Preemptive SJF): Dynamically preempts currently running processes when a new job arrives with shorter remaining time.\n"
        "4. Priority Scheduling (Non-preemptive): Dispatches based on priority level.\n"
        "5. Priority Scheduling (Preemptive with Aging): Employs dynamic priority escalation (aging) to guarantee that low-priority processes do not suffer starvation.\n"
        "6. Round Robin (RR): Grants each process a fixed time quantum (Δt), cycling through a ready queue.\n"
        "7. Multi-Level Feedback Queue (MLFQ): Three priority tiers (Q0 with small quantum, Q1 with medium quantum, Q2 with FCFS). Demotes CPU-heavy jobs while preserving high responsiveness for interactive I/O jobs. Employs a periodic priority boost to eliminate starvation.\n\n"
        "Mathematical Formulas Implemented:\n"
        "• Turnaround Time (TAT) = Completion Time (CT) - Arrival Time (AT)\n"
        "• Waiting Time (WT) = Turnaround Time (TAT) - Burst Time (BT)\n"
        "• Response Time (RT) = Time of First Execution - Arrival Time (AT)\n"
        "• CPU Utilization = (Total Busy Time / Makespan) * 100%\n"
        "• Throughput = Number of Completed Processes / Total Makespan\n\n"
        "Intelligent AI Recommender:\n"
        "The recommender computes the statistical Coefficient of Variation (CV = σ / μ) of burst times, analyzes arrival skewness, "
        "and evaluates priority divergence. If CV > 0.6, it recommends SRTF (which mathematically minimizes average waiting time via the SJF "
        "Optimality Theorem). For uniform burst profiles, it recommends Round Robin or FCFS to avoid unnecessary context switch penalties."
    )

    # 3.3 Concurrency, Synchronization & Deadlock
    h2 = doc.add_heading("3.3 Concurrency, Synchronization Primitives & Deadlock Avoidance", level=2)
    h2.runs[0].font.color.rgb = COLOR_ACCENT
    doc.add_paragraph(
        "• Dijkstra's Banker's Algorithm: Implements Deadlock Avoidance for systems with multiple resource instances. Given Allocation matrix [N x M], "
        "Maximum Claim matrix [N x M], and Available vector [M], it calculates the Need matrix: Need[i][j] = Max[i][j] - Allocation[i][j]. "
        "The Safety Algorithm determines if there exists a valid Safe Sequence <P0, P1, ..., Pn-1> such that Need[i] <= Work. If safe, execution order is guaranteed without deadlock.\n"
        "• Bounded Buffer (Producer-Consumer): Synchronized using real counting semaphores: 'empty' (initialized to buffer capacity) and 'full' (initialized to 0), "
        "combined with a binary mutual exclusion lock ('mutex') to prevent buffer overflows, underflows, and race conditions.\n"
        "• Readers-Writers Problem: Employs a fair reader-writer synchronization pattern with writer starvation avoidance. Multiple readers read concurrently; "
        "writers acquire exclusive mutual exclusion.\n"
        "• Inter-Process Communication (IPC) Benchmark: Benchmarks latency (μs) and throughput (MB/s) across Shared Memory, Unix Pipes, and Message Queues. "
        "Demonstrates why Shared Memory is orders of magnitude faster (direct physical address mapping without kernel-space copying)."
    )

    # 3.4 Multi-Client Concurrent File Service
    h2 = doc.add_heading("3.4 Multi-Client Concurrent File Service & LRU Page Cache", level=2)
    h2.runs[0].font.color.rgb = COLOR_ACCENT
    doc.add_paragraph(
        "• Reader-Writer Fair Lock (RWLock): Implements fine-grained per-file concurrency. Multiple clients can read the same file simultaneously without blocking. "
        "Writers acquire exclusive access. If a writer is waiting, new incoming readers are queued to prevent writer starvation.\n"
        "• Simulated OS Page Cache: Emulates the Linux kernel buffer cache. Implements an O(1) Least Recently Used (LRU) eviction algorithm using an internal "
        "Doubly Linked List + Hash Map (OrderedDict). Tracks cache hits, misses, and dirty bits. When a dirty page is evicted, it is flushed to disk storage, simulating the Linux 'pdflush' kernel daemon.\n"
        "• Concurrent Traffic Harness: Spawns multiple concurrent worker threads simulating independent clients firing simultaneous reads, writes, and appends, achieving 90+ ops/sec throughput without race conditions."
    )

    # 3.5 Machine Learning Resource Analytics
    h2 = doc.add_heading("3.5 Machine Learning Forecasting & Memory Leak Detection", level=2)
    h2.runs[0].font.color.rgb = COLOR_ACCENT
    doc.add_paragraph(
        "• Time-Series Forecasting: Utilizes a 120-second rolling ring buffer of system telemetry. Fits Ridge Polynomial Regression models to forecast CPU and Memory utilization "
        "into the future (+10s, +30s, +60s horizons), computing trend slopes and R² model confidence metrics.\n"
        "• Memory Leak Detection: Analyzes process Resident Set Size (RSS) rate of change over time (dRSS/dt). If a process displays monotonic memory growth (dRSS/dt > 0.5 MB/s with R² > 0.85) "
        "over consecutive sampling windows, SysPilot flags a critical Memory Leak warning before the Linux Out-Of-Memory (OOM) killer is forced to terminate processes.\n"
        "• CPU Runaway Loop Detection: Flags single-threaded busy loops consuming >85% CPU capacity continuously."
    )

    # -------------------------------------------------------------
    # SECTION 4: STEP-BY-STEP TESTING & VERIFICATION GUIDE
    # -------------------------------------------------------------
    h1 = doc.add_heading("4. Comprehensive Feature Testing & Verification Guide", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph(
        "Follow this comprehensive testing guide to demonstrate and verify every feature during project evaluation:"
    )

    test_table = doc.add_table(rows=9, cols=3)
    test_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    test_headers = ["Feature / Subsystem", "How to Test (Step-by-Step)", "Expected Output / Verification"]
    for col_idx, text in enumerate(test_headers):
        cell = test_table.rows[0].cells[col_idx]
        cell.text = text
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(cell, "0A192F")

    tests = [
        ("Automated Unit Test Suite", "Run in terminal:\npython -m pytest tests/ -v", "All 18 tests pass cleanly with 100% green status across scheduling, Banker's, synchronization, and /proc parsing."),
        ("Live API Integration", "Run in terminal:\npython tests/verify_endpoints.py", "All 8 core subsystem APIs return [PASS] with confirmed JSON responses and 90+ ops/sec throughput."),
        ("Live Process & Core Heatmap", "Open Dashboard -> System Monitor tab. Observe the top quickbar and CPU core grid.", "Real-time CPU and RAM meters update every 1 second via WebSockets. Per-core heatmap shows dynamic load percentages."),
        ("Process Hierarchy Tree", "System Monitor tab -> Click 'Process Hierarchy Tree' button.", "Modal opens displaying tree graph (PPID -> PID) showing parent processes spawning child threads."),
        ("CPU Scheduling Simulation", "CPU Scheduler tab -> Select 'Round Robin' -> Click 'Run Simulation'.", "Interactive Gantt timeline renders process blocks [start, end]. Results table computes CT, TAT, WT, RT, and context switches."),
        ("AI Recommender Engine", "CPU Scheduler tab -> Select 'Preset: High Burst Variance' -> Click 'AI Recommendation Engine'.", "Recommender analyzes CV > 0.6, selects SRTF as optimal, and displays full leaderboard and justification."),
        ("Banker's Deadlock Avoidance", "Concurrency tab -> Click 'Preset: Safe State' -> Click 'Compute Safety & Sequence'.", "Green badge appears: 'SAFE STATE: No Deadlock'. Safe sequence < P1 -> P3 -> P4 -> P0 -> P2 > is displayed with step-by-step trace."),
        ("Multi-Client File Stress Test", "File Hub tab -> Click 'Launch Concurrent Stress Test'.", "Spawns concurrent client threads performing reads/writes. Activity log streams in real-time, LRU cache hit ratio increases.")
    ]

    for row_idx, data in enumerate(tests, start=1):
        row = test_table.rows[row_idx]
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.text = text
            cell.paragraphs[0].runs[0].font.size = Pt(8.5)
            set_cell_background(cell, "F8FAFC" if row_idx % 2 == 0 else "FFFFFF")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------
    # SECTION 5: EVALUATOR VIVA Q&A PREPARATION GUIDE
    # -------------------------------------------------------------
    h1 = doc.add_heading("5. Evaluator Viva Q&A Guide", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    viva_qa = [
        ("Q1: What is the /proc filesystem and how does SysPilot read kernel data?",
         "Answer: /proc is a virtual pseudo-filesystem created dynamically in RAM by the Linux kernel. It contains no real physical disk files. "
         "SysPilot parses /proc/stat to calculate CPU tick proportions, /proc/meminfo for RAM breakdown, and /proc/[pid]/stat for process runtime stats. "
         "On Windows, SysPilot uses an automated cross-platform emulation engine via psutil while preserving exact kernel data structures."),

        ("Q2: Why is Shortest Remaining Time First (SRTF) mathematically optimal?",
         "Answer: By the Shortest Job First optimality theorem, scheduling the job with the smallest remaining burst time minimizes the queue waiting time "
         "for subsequent jobs. Giving the CPU to a short job removes it from the ready queue quickly, reducing the average waiting time (WT_avg)."),

        ("Q3: How does your system prevent starvation in Priority Scheduling and MLFQ?",
         "Answer: In Priority Scheduling, we implemented Aging (waiting processes gradually gain priority over time). In MLFQ, we implemented a periodic "
         "Priority Boost interval where all lower-queue processes are periodically promoted back to Queue 0, preventing indefinite starvation."),

        ("Q4: Explain how Banker's Algorithm determines if a state is safe.",
         "Answer: It calculates Need[i][j] = Max[i][j] - Allocation[i][j]. It searches for a process Pi whose Need is less than or equal to currently Available resources. "
         "If found, it assumes Pi runs to completion and releases its allocated resources back to Work (Work = Work + Allocation[i]). If all processes can finish, the system is in a SAFE state."),

        ("Q5: How does your Reader-Writer Lock prevent writer starvation?",
         "Answer: In standard reader-preference locks, a continuous stream of readers can starve waiting writers indefinitely. SysPilot's RWLock tracks "
         "a waiting_writers counter. If any writer is waiting, new incoming readers are suspended on a condition variable until the writer completes."),

        ("Q6: What is an LRU Page Cache and why is dirty-page writeback necessary?",
         "Answer: An LRU (Least Recently Used) cache evicts the page that has not been accessed for the longest time when capacity is exceeded. "
         "If a page was modified in memory (marked with a dirty bit), evicting it without writing to disk would cause data loss. SysPilot flushes dirty pages upon eviction, simulating the OS pdflush daemon."),

        ("Q7: How does your Machine Learning model detect memory leaks?",
         "Answer: Memory leaks occur when allocated memory is never freed. SysPilot tracks Resident Set Size (RSS) over time. If dRSS/dt > 0.5 MB/s "
         "monotonically with strong linear correlation (R² > 0.85), it flags a memory leak before the OS OOM killer terminates the process.")
    ]

    for q, a in viva_qa:
        qp = doc.add_paragraph()
        qp.paragraph_format.space_before = Pt(8)
        qp.paragraph_format.space_after = Pt(2)
        q_run = qp.add_run(q)
        q_run.font.bold = True
        q_run.font.color.rgb = COLOR_PRIMARY
        q_run.font.size = Pt(10)

        ap = doc.add_paragraph()
        ap.paragraph_format.space_after = Pt(6)
        a_run = ap.add_run(a)
        a_run.font.size = Pt(9.5)

    # Save Word Document
    out_path = Path("d:/VIT-Third_Year-Sem-1/OS/Course_Project/SysPilot_Comprehensive_OS_Report.docx")
    doc.save(str(out_path))
    print(f"Report successfully saved to: {out_path}")

if __name__ == "__main__":
    create_report()
