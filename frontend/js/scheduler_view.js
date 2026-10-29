/**
 * CPU Scheduling Studio & AI Recommender View.
 * Handles workload definition, interactive Gantt chart rendering,
 * comparative benchmarking, and workload-driven intelligent recommendations.
 */

class SchedulerView {
  constructor() {
    this.tableBody = document.getElementById("scheduler-proc-rows");
    this.resultsBody = document.getElementById("scheduler-results-body");
    this.presetSelect = document.getElementById("workload-preset-select");
    this.btnAddProc = document.getElementById("btn-add-proc-row");
    this.btnRun = document.getElementById("btn-run-simulation");
    this.btnCompare = document.getElementById("btn-compare-all");
    this.btnRecommend = document.getElementById("btn-ai-recommend");
    this.algoSelect = document.getElementById("selected-algorithm");
    this.quantumInput = document.getElementById("quantum-input");
    this.mlfqBoostInput = document.getElementById("mlfq-boost-input");

    this.timelineBar = document.getElementById("gantt-timeline-bar");
    this.ticksBar = document.getElementById("gantt-ticks-bar");
    this.makespanBadge = document.getElementById("gantt-makespan-badge");

    this.palette = [
      "#00f2fe", "#4facfe", "#b388ff", "#00e676", "#ffab00",
      "#ff1744", "#ff4081", "#7c4dff", "#00b0ff", "#1de9b6"
    ];

    // Initialize visualizers
    this.ganttChart = null;
    this.stateVisualizer = null;
    this.metricsTracker = null;

    this.initPresets();
    this.initListeners();
    this.initSimulationController();
    this.loadPreset("standard");
  }

  initSimulationController() {
    // Subscribe to simulation events
    window.simulationController.subscribe((data) => {
      if (data.type === "SIMULATION_EVENT") {
        this.onSimulationEvent(data.event);
      } else if (data.type === "SIMULATION_COMPLETE") {
        this.onSimulationComplete(data);
      } else if (data.type === "SIMULATION_RESET") {
        this.onSimulationReset();
      } else if (data.type === "STATE_CHANGED") {
        this.onStateChanged(data.state);
      }
    });
  }

  onSimulationEvent(event) {
    // Forward to visualizers
    if (this.ganttChart) {
      this.ganttChart.onEvent(event);
    }
    if (this.stateVisualizer) {
      this.stateVisualizer.onEvent(event);
    }
    if (this.metricsTracker) {
      this.metricsTracker.onEvent(event);
    }
  }

  onSimulationComplete(data) {
    if (this.ganttChart) {
      this.ganttChart.finalize();
    }
    this.makespanBadge.textContent = `Makespan: ${data.makespan} time units`;
    window.app.showToast("Simulation complete", "success");
  }

  onSimulationReset() {
    if (this.ganttChart) {
      this.ganttChart.reset();
    }
    if (this.stateVisualizer) {
      this.stateVisualizer.reset();
    }
    if (this.metricsTracker) {
      this.metricsTracker.reset();
    }
    this.makespanBadge.textContent = "Makespan: -- time units";
  }

  onStateChanged(state) {
    // Update UI based on simulation state
    const btnPlay = document.getElementById("btn-sim-play");
    const btnPause = document.getElementById("btn-sim-pause");

    if (btnPlay && btnPause) {
      if (state === "RUNNING") {
        btnPlay.disabled = true;
        btnPause.disabled = false;
      } else if (state === "PAUSED") {
        btnPlay.disabled = false;
        btnPause.disabled = false;
      } else {
        btnPlay.disabled = false;
        btnPause.disabled = true;
      }
    }
  }

  initPresets() {
    this.presets = {
      standard: [
        { pid: 1, name: "P1", arrival_time: 0, burst_time: 5, priority: 2 },
        { pid: 2, name: "P2", arrival_time: 1, burst_time: 3, priority: 1 },
        { pid: 3, name: "P3", arrival_time: 2, burst_time: 8, priority: 4 },
        { pid: 4, name: "P4", arrival_time: 3, burst_time: 2, priority: 3 },
        { pid: 5, name: "P5", arrival_time: 4, burst_time: 4, priority: 2 }
      ],
      high_variance: [
        { pid: 1, name: "Web_Request", arrival_time: 0, burst_time: 2, priority: 2 },
        { pid: 2, name: "DB_Backup", arrival_time: 1, burst_time: 24, priority: 5 },
        { pid: 3, name: "Cache_Check", arrival_time: 2, burst_time: 1, priority: 1 },
        { pid: 4, name: "Data_Mining", arrival_time: 3, burst_time: 18, priority: 4 },
        { pid: 5, name: "Auth_Verify", arrival_time: 4, burst_time: 3, priority: 2 }
      ],
      interactive: [
        { pid: 1, name: "Text_Editor", arrival_time: 0, burst_time: 4, priority: 1 },
        { pid: 2, name: "Browser_Tab", arrival_time: 1, burst_time: 6, priority: 2 },
        { pid: 3, name: "Audio_Daemon", arrival_time: 2, burst_time: 3, priority: 1 },
        { pid: 4, name: "Terminal", arrival_time: 3, burst_time: 5, priority: 2 }
      ],
      priority_heavy: [
        { pid: 1, name: "Kernel_Watchdog", arrival_time: 0, burst_time: 4, priority: 1 },
        { pid: 2, name: "User_Render", arrival_time: 1, burst_time: 7, priority: 5 },
        { pid: 3, name: "Network_IRQ", arrival_time: 2, burst_time: 3, priority: 1 },
        { pid: 4, name: "Batch_Compress", arrival_time: 3, burst_time: 10, priority: 8 }
      ],
      convoy: [
        { pid: 1, name: "Giant_Job_P1", arrival_time: 0, burst_time: 25, priority: 3 },
        { pid: 2, name: "Tiny_Job_P2", arrival_time: 1, burst_time: 2, priority: 2 },
        { pid: 3, name: "Tiny_Job_P3", arrival_time: 2, burst_time: 1, priority: 1 },
        { pid: 4, name: "Tiny_Job_P4", arrival_time: 3, burst_time: 2, priority: 2 }
      ]
    };
  }

  initListeners() {
    this.presetSelect.addEventListener("change", (e) => this.loadPreset(e.target.value));
    this.btnAddProc.addEventListener("click", () => this.addProcessRow());
    this.btnRun.addEventListener("click", () => this.runSimulation());
    this.btnCompare.addEventListener("click", () => this.compareAll());
    this.btnRecommend.addEventListener("click", () => this.getRecommendation());
  }

  loadPreset(name) {
    const list = this.presets[name] || this.presets["standard"];
    this.tableBody.innerHTML = "";
    list.forEach(p => this.addProcessRow(p.pid, p.name, p.arrival_time, p.burst_time, p.priority));
  }

  addProcessRow(pid, name, arrival, burst, priority) {
    const currentRows = this.tableBody.querySelectorAll("tr").length;
    const pIdVal = pid !== undefined ? pid : currentRows + 1;
    const nameVal = name || `P${pIdVal}`;
    const arrVal = arrival !== undefined ? arrival : 0;
    const burstVal = burst !== undefined ? burst : 4;
    const prioVal = priority !== undefined ? priority : 1;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="number" class="form-control mono proc-pid" value="${pIdVal}" style="width: 55px;"></td>
      <td><input type="text" class="form-control proc-name" value="${nameVal}" style="width: 110px;"></td>
      <td><input type="number" class="form-control mono proc-at" value="${arrVal}" min="0" style="width: 65px;"></td>
      <td><input type="number" class="form-control mono proc-bt" value="${burstVal}" min="1" style="width: 65px;"></td>
      <td><input type="number" class="form-control mono proc-prio" value="${prioVal}" min="0" style="width: 65px;"></td>
      <td><button class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">&times;</button></td>
    `;
    this.tableBody.appendChild(tr);
  }

  getProcessesFromInput() {
    const rows = this.tableBody.querySelectorAll("tr");
    const processes = [];
    rows.forEach(r => {
      const pid = parseInt(r.querySelector(".proc-pid").value, 10);
      const name = r.querySelector(".proc-name").value.trim();
      const arrival = parseInt(r.querySelector(".proc-at").value, 10) || 0;
      const burst = parseInt(r.querySelector(".proc-bt").value, 10) || 1;
      const priority = parseInt(r.querySelector(".proc-prio").value, 10) || 0;
      processes.push({ pid, name, arrival_time: arrival, burst_time: burst, priority });
    });
    return processes;
  }

  async runSimulation() {
    const processes = this.getProcessesFromInput();
    if (processes.length === 0) {
      window.app.showToast("Please define at least one process.", "error");
      return;
    }

    const algo = this.algoSelect.value;
    const quantum = parseInt(this.quantumInput.value, 10) || 2;
    const boost = parseInt(this.mlfqBoostInput.value, 10) || 20;

    // Initialize visualizers
    if (!this.ganttChart) {
      this.ganttChart = new LiveGanttChart("gantt-timeline-bar", "gantt-ticks-bar");
    }
    if (!this.stateVisualizer) {
      this.stateVisualizer = new ProcessStateVisualizer();
      window.processStateVisualizer = this.stateVisualizer;
    }

    // Reset visualizers
    this.ganttChart.reset();
    this.stateVisualizer.reset();

    // Start real-time simulation
    try {
      await window.simulationController.start(algo, processes, {
        quantum: quantum,
        q0_quantum: quantum,
        q1_quantum: quantum * 2,
        boost_interval: boost,
        aging_rate: 1
      });
      window.app.showToast("Simulation started", "success");
    } catch (err) {
      window.app.showToast("Failed to start simulation: " + err.message, "error");
    }
  }

  renderGantt(timeline, makespan) {
    this.timelineBar.innerHTML = "";
    this.ticksBar.innerHTML = "";
    this.makespanBadge.textContent = `Makespan: ${makespan} time units`;

    if (!timeline || timeline.length === 0) return;

    // Build timeline blocks
    timeline.forEach(block => {
      const duration = block.end - block.start;
      const widthPct = (duration / makespan) * 100;
      const div = document.createElement("div");
      div.className = "gantt-block";
      div.style.width = `${widthPct}%`;

      if (block.pid === "IDLE") {
        div.classList.add("idle");
        div.innerHTML = `<span style="font-size: 0.72rem;">IDLE</span><span style="font-size: 0.65rem;">Δ${duration}</span>`;
      } else {
        const colorIdx = (block.pid * 2) % this.palette.length;
        div.style.background = this.palette[colorIdx];
        div.innerHTML = `<span>${block.name}</span><span style="font-size: 0.68rem; opacity: 0.85;">[${block.start} - ${block.end}]</span>`;
      }
      div.title = `${block.name}: Time ${block.start} to ${block.end} (Duration: ${duration})`;
      this.timelineBar.appendChild(div);
    });

    // Build tick markers
    let tickHtml = `<span>0</span>`;
    timeline.forEach(b => {
      tickHtml += `<span>${b.end}</span>`;
    });
    this.ticksBar.innerHTML = tickHtml;
  }

  renderResultsTable(metrics) {
    this.resultsBody.innerHTML = "";
    if (!metrics || !metrics.process_metrics) return;

    metrics.process_metrics.forEach(p => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="mono"><strong>${p.pid}</strong></td>
        <td><strong>${p.name}</strong></td>
        <td class="mono">${p.arrival_time}</td>
        <td class="mono">${p.burst_time}</td>
        <td class="mono">${p.completion_time}</td>
        <td class="mono" style="color: var(--accent-purple); font-weight: 600;">${p.turnaround_time}</td>
        <td class="mono" style="color: var(--accent-cyan); font-weight: 600;">${p.waiting_time}</td>
        <td class="mono" style="color: var(--accent-emerald);">${p.response_time}</td>
      `;
      this.resultsBody.appendChild(tr);
    });

    // Summary footer row
    const footerTr = document.createElement("tr");
    footerTr.style.background = "rgba(255, 255, 255, 0.05)";
    footerTr.innerHTML = `
      <td colspan="5"><strong>Averages &amp; System Performance:</strong></td>
      <td class="mono" style="color: var(--accent-purple); font-weight: 700;">Avg TAT: ${metrics.avg_turnaround_time}</td>
      <td class="mono" style="color: var(--accent-cyan); font-weight: 700;">Avg WT: ${metrics.avg_waiting_time}</td>
      <td class="mono" style="color: var(--accent-emerald); font-weight: 700;">Avg RT: ${metrics.avg_response_time}</td>
    `;
    this.resultsBody.appendChild(footerTr);
  }

  async compareAll() {
    const processes = this.getProcessesFromInput();
    if (processes.length === 0) return;

    const quantum = parseInt(this.quantumInput.value, 10) || 2;
    try {
      const res = await fetch("/api/scheduler/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          processes: processes,
          params: { quantum: quantum }
        })
      });
      const leaderboard = await res.json();
      this.renderLeaderboard(leaderboard);
    } catch (e) {
      window.app.showToast("Failed to compare algorithms", "error");
    }
  }

  renderLeaderboard(leaderboard) {
    const compCard = document.getElementById("comparison-card");
    const compBody = document.getElementById("comparison-table-body");
    compCard.style.display = "block";
    compBody.innerHTML = "";

    leaderboard.forEach((entry, idx) => {
      const tr = document.createElement("tr");
      const isWinner = idx === 0;
      if (isWinner) tr.style.background = "rgba(0, 242, 254, 0.08)";

      tr.innerHTML = `
        <td class="mono"><strong>#${idx + 1}</strong> ${isWinner ? '👑' : ''}</td>
        <td><strong>${entry.algorithm_name}</strong></td>
        <td class="mono" style="color: var(--accent-cyan); font-weight: 700;">${entry.avg_waiting_time}</td>
        <td class="mono">${entry.avg_turnaround_time}</td>
        <td class="mono">${entry.avg_response_time}</td>
        <td class="mono">${entry.context_switches}</td>
        <td class="mono">${entry.cpu_utilization}%</td>
        <td class="mono">${entry.throughput}</td>
      `;
      compBody.appendChild(tr);
    });

    compCard.scrollIntoView({ behavior: 'smooth' });
  }

  async getRecommendation() {
    const processes = this.getProcessesFromInput();
    if (processes.length === 0) return;

    const quantum = parseInt(this.quantumInput.value, 10) || 2;
    try {
      const res = await fetch("/api/scheduler/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          processes: processes,
          params: { quantum: quantum }
        })
      });
      const data = await res.json();

      document.getElementById("rec-algo-title").textContent = `Recommended: ${data.recommended_algorithm.name}`;
      document.getElementById("rec-avg-wt").textContent = `${data.recommended_algorithm.avg_waiting_time}`;
      document.getElementById("rec-avg-tat").textContent = `${data.recommended_algorithm.avg_turnaround_time}`;
      document.getElementById("rec-cs-count").textContent = `${data.recommended_algorithm.context_switches}`;

      const listContainer = document.getElementById("rec-justification-list");
      listContainer.innerHTML = "";
      data.justification.forEach(item => {
        const p = document.createElement("div");
        p.innerHTML = `<span style="color: var(--accent-cyan);">✓</span> ${item}`;
        listContainer.appendChild(p);
      });
      data.trade_offs.forEach(item => {
        const p = document.createElement("div");
        p.innerHTML = `<span style="color: var(--accent-amber);">ℹ</span> ${item}`;
        listContainer.appendChild(p);
      });

      this.renderLeaderboard(data.leaderboard);
      window.app.showToast("AI Recommendation Generated!", "success");
    } catch (e) {
      window.app.showToast("Failed to compute recommendation", "error");
    }
  }
}

window.schedulerView = new SchedulerView();
