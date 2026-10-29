/**
 * Process View & Linux Kernel Inspector.
 * Manages process table, core heatmaps, signal dispatching, renicing, and tree hierarchy.
 */

class ProcessView {
  constructor() {
    this.tableBody = document.getElementById("process-table-body");
    this.coreGrid = document.getElementById("cpu-core-grid");
    this.searchInput = document.getElementById("proc-search-input");
    this.sortSelect = document.getElementById("proc-sort-select");
    this.btnRefresh = document.getElementById("btn-refresh-procs");
    this.activeModalPid = null;

    this.initListeners();
  }

  initListeners() {
    this.btnRefresh.addEventListener("click", () => this.fetchProcesses());
    this.searchInput.addEventListener("input", () => this.filterTable());
    this.sortSelect.addEventListener("change", () => this.fetchProcesses());

    // Tree modal
    document.getElementById("btn-open-tree").addEventListener("click", () => this.fetchProcessTree());
    // Zombie scanner
    document.getElementById("btn-scan-zombies").addEventListener("click", () => this.scanZombies());
    // Raw proc
    document.getElementById("btn-raw-proc").addEventListener("click", () => this.fetchRawProc());

    // Signal buttons in action modal
    document.querySelectorAll("#modal-process-action button[data-sig]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const sig = e.target.getAttribute("data-sig");
        this.sendSignal(this.activeModalPid, sig);
      });
    });

    // Renice button
    document.getElementById("btn-apply-renice").addEventListener("click", () => {
      const niceVal = parseInt(document.getElementById("modal-nice-input").value, 10);
      this.applyRenice(this.activeModalPid, niceVal);
    });

    // Listen to WebSocket telemetry for core heatmaps
    window.telemetryWs.subscribe((data) => {
      if (data.system && data.system.cpu) {
        this.renderCoreHeatmap(data.system.cpu.per_core_percent);
      }
    });

    // Initial fetch
    this.fetchProcesses();
  }

  renderCoreHeatmap(corePercentages) {
    if (!corePercentages || !this.coreGrid) return;
    
    // Check if cells exist, otherwise generate
    if (this.coreGrid.children.length !== corePercentages.length) {
      this.coreGrid.innerHTML = "";
      corePercentages.forEach((_, idx) => {
        const cell = document.createElement("div");
        cell.className = "core-cell";
        cell.id = `core-cell-${idx}`;
        cell.innerHTML = `
          <div class="core-cell-name">Core ${idx}</div>
          <div class="core-cell-val" id="core-val-${idx}">0.0%</div>
        `;
        this.coreGrid.appendChild(cell);
      });
    }

    // Update cells with dynamic color intensity
    corePercentages.forEach((pct, idx) => {
      const cell = document.getElementById(`core-cell-${idx}`);
      const valEl = document.getElementById(`core-val-${idx}`);
      if (valEl) valEl.textContent = `${pct.toFixed(0)}%`;

      if (cell) {
        // Color interpolate from deep blue/cyan to amber/rose
        if (pct < 40) {
          cell.style.borderColor = "rgba(0, 242, 254, 0.3)";
          cell.style.background = `rgba(0, 242, 254, ${Math.max(0.04, pct / 400)})`;
          if (valEl) valEl.style.color = "var(--accent-cyan)";
        } else if (pct < 75) {
          cell.style.borderColor = "rgba(255, 171, 0, 0.4)";
          cell.style.background = `rgba(255, 171, 0, ${Math.max(0.1, pct / 300)})`;
          if (valEl) valEl.style.color = "var(--accent-amber)";
        } else {
          cell.style.borderColor = "rgba(255, 23, 68, 0.6)";
          cell.style.background = `rgba(255, 23, 68, ${Math.max(0.15, pct / 200)})`;
          if (valEl) valEl.style.color = "var(--accent-rose)";
        }
      }
    });
  }

  async fetchProcesses() {
    const sortBy = this.sortSelect.value;
    try {
      const res = await fetch(`/api/processes?limit=60&sort_by=${sortBy}`);
      const data = await res.json();
      this.currentProcesses = data;
      this.renderTable(data);
    } catch (err) {
      console.error("Failed to fetch processes:", err);
    }
  }

  renderTable(processes) {
    if (!this.tableBody) return;
    this.tableBody.innerHTML = "";

    if (processes.length === 0) {
      this.tableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted);">No processes found.</td></tr>`;
      return;
    }

    processes.forEach(p => {
      const tr = document.createElement("tr");
      
      let statusBadgeClass = "badge-sleeping";
      if (p.status.toLowerCase().includes("running")) statusBadgeClass = "badge-running";
      else if (p.status.toLowerCase().includes("zombie")) statusBadgeClass = "badge-zombie";
      else if (p.status.toLowerCase().includes("stopped")) statusBadgeClass = "badge-stopped";

      tr.innerHTML = `
        <td class="mono"><strong>${p.pid}</strong></td>
        <td class="mono" style="color: var(--text-muted);">${p.ppid}</td>
        <td><strong>${this.escapeHtml(p.name)}</strong></td>
        <td style="color: var(--text-secondary);">${p.username}</td>
        <td><span class="badge ${statusBadgeClass}">${p.status}</span></td>
        <td class="mono" style="color: ${p.cpu_percent > 50 ? 'var(--accent-rose)' : 'var(--text-primary)'}; font-weight: 600;">${p.cpu_percent}%</td>
        <td class="mono">${p.memory_percent}%</td>
        <td class="mono" style="color: var(--text-muted);">${p.rss_formatted}</td>
        <td class="mono">${p.nice}</td>
        <td>
          <button class="btn btn-secondary btn-sm btn-proc-ctrl" data-pid="${p.pid}" data-name="${encodeURIComponent(p.name)}" data-nice="${p.nice}">
            Control
          </button>
        </td>
      `;
      this.tableBody.appendChild(tr);
    });

    // Attach click listeners to all Control buttons
    this.tableBody.querySelectorAll(".btn-proc-ctrl").forEach(btn => {
      btn.addEventListener("click", () => {
        const pid = parseInt(btn.getAttribute("data-pid"), 10);
        const name = decodeURIComponent(btn.getAttribute("data-name"));
        const nice = parseInt(btn.getAttribute("data-nice"), 10);
        this.openActionModal(pid, name, nice);
      });
    });
  }

  filterTable() {
    const q = this.searchInput.value.toLowerCase().trim();
    if (!this.currentProcesses) return;
    if (!q) {
      this.renderTable(this.currentProcesses);
      return;
    }
    const filtered = this.currentProcesses.filter(p => 
      p.pid.toString().includes(q) || p.name.toLowerCase().includes(q)
    );
    this.renderTable(filtered);
  }

  openActionModal(pid, name, nice) {
    this.activeModalPid = pid;
    document.getElementById("modal-proc-pid").textContent = `PID: ${pid}`;
    document.getElementById("modal-proc-name").textContent = `Process: ${name}`;
    document.getElementById("modal-nice-input").value = nice || 0;
    
    window.app.openModal("modal-process-action");
  }

  async sendSignal(pid, sigName) {
    if (!pid) return;
    try {
      const res = await fetch("/api/processes/signal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pid, signal_name: sigName })
      });
      const data = await res.json();
      if (res.ok) {
        window.app.showToast(`Signal ${sigName} dispatched to PID ${pid}`, "success");
        window.app.closeModal("modal-process-action");
        this.fetchProcesses();
      } else {
        window.app.showToast(data.detail || "Signal failed", "error");
      }
    } catch (e) {
      window.app.showToast("Network error dispatching signal", "error");
    }
  }

  async applyRenice(pid, niceVal) {
    if (!pid) return;
    try {
      const res = await fetch("/api/processes/renice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pid, nice_value: niceVal })
      });
      const data = await res.json();
      if (res.ok) {
        window.app.showToast(`PID ${pid} reniced to ${niceVal}`, "success");
        window.app.closeModal("modal-process-action");
        this.fetchProcesses();
      } else {
        window.app.showToast(data.detail || "Renice failed", "error");
      }
    } catch (e) {
      window.app.showToast("Network error during renice", "error");
    }
  }

  async fetchProcessTree() {
    const container = document.getElementById("tree-container");
    container.innerHTML = "Tracing parent-child process tree...";
    window.app.openModal("modal-process-tree");

    try {
      const res = await fetch("/api/processes/tree");
      const data = await res.json();
      container.innerHTML = "";
      
      const renderNode = (node, depth = 0) => {
        const indent = "&nbsp;&nbsp;&nbsp;&nbsp;".repeat(depth);
        const prefix = depth > 0 ? "└── " : "▶ ";
        const item = document.createElement("div");
        item.style.padding = "2px 0";
        item.innerHTML = `${indent}<span style="color: var(--accent-cyan);">${prefix}</span><strong>[${node.pid}]</strong> ${this.escapeHtml(node.name)} <span style="font-size: 0.75rem; color: var(--text-muted);">(CPU: ${node.cpu_percent}%, RAM: ${node.memory_percent}%)</span>`;
        container.appendChild(item);

        if (node.children && node.children.length > 0) {
          node.children.slice(0, 10).forEach(c => renderNode(c, depth + 1));
          if (node.children.length > 10) {
            const more = document.createElement("div");
            more.innerHTML = `${indent}&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: var(--text-muted); font-size: 0.75rem;">... and ${node.children.length - 10} more sub-threads/children</span>`;
            container.appendChild(more);
          }
        }
      };

      data.roots.forEach(r => renderNode(r, 0));
    } catch (e) {
      container.innerHTML = "Failed to load process tree.";
    }
  }

  async scanZombies() {
    try {
      const res = await fetch("/api/processes/zombies");
      const data = await res.json();
      const alertBox = document.getElementById("zombie-alert-box");
      const alertText = document.getElementById("zombie-alert-text");

      alertBox.style.display = "block";
      if (data.zombies_count === 0 && data.orphans_count === 0) {
        alertBox.style.background = "rgba(0, 230, 118, 0.1)";
        alertBox.style.borderColor = "rgba(0, 230, 118, 0.3)";
        alertText.innerHTML = `<span style="color: var(--accent-emerald);">Kernel Scan Clear:</span> No zombie or orphan processes detected. System reaping operating normally.`;
      } else {
        alertBox.style.background = "rgba(255, 23, 68, 0.1)";
        alertBox.style.borderColor = "rgba(255, 23, 68, 0.3)";
        alertText.innerHTML = `Found <strong>${data.zombies_count}</strong> zombie(s) and <strong>${data.orphans_count}</strong> orphan(s) requiring parent reaping.`;
      }
    } catch (e) {
      console.error(e);
    }
  }

  async fetchRawProc() {
    const pre = document.getElementById("raw-proc-content");
    pre.textContent = "Loading raw kernel /proc virtual filesystem structures...";
    window.app.openModal("modal-raw-proc");

    try {
      const res = await fetch("/api/system/proc_info");
      const data = await res.json();
      pre.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      pre.textContent = "Error loading /proc data.";
    }
  }

  escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
}

window.processView = new ProcessView();
