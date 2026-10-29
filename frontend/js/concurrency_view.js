/**
 * Concurrency, Deadlock & IPC Lab View.
 * Implements interactive Banker's algorithm safe sequence visualizer,
 * Bounded Buffer animation, Readers-Writers synchronization, and IPC benchmarks.
 */

class ConcurrencyView {
  constructor() {
    this.initBankers();
    this.initSync();
    this.initIPC();
  }

  initBankers() {
    this.allocTable = document.getElementById("bankers-alloc-table");
    this.maxTable = document.getElementById("bankers-max-table");

    document.getElementById("btn-load-bankers-safe").addEventListener("click", () => this.loadBankersPreset("safe"));
    document.getElementById("btn-load-bankers-unsafe").addEventListener("click", () => this.loadBankersPreset("unsafe"));
    document.getElementById("btn-run-bankers").addEventListener("click", () => this.runBankersSafety());

    this.loadBankersPreset("safe");
  }

  loadBankersPreset(type) {
    let avail, alloc, max;

    if (type === "safe") {
      // Classic Silberschatz textbook safe state (5 processes, 3 resources)
      avail = [3, 3, 2];
      alloc = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
      ];
      max = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
      ];
    } else {
      // Unsafe deadlocked state (resource shortage)
      avail = [0, 0, 0];
      alloc = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
      ];
      max = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [4, 2, 2],
        [4, 3, 3]
      ];
    }

    // Set available
    document.getElementById("avail-0").value = avail[0];
    document.getElementById("avail-1").value = avail[1];
    document.getElementById("avail-2").value = avail[2];

    // Build Alloc Table
    this.allocTable.innerHTML = "";
    for (let i = 0; i < 5; i++) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color: var(--text-muted);">P${i}</td>
        <td><input type="number" class="alloc-input mono" data-row="${i}" data-col="0" value="${alloc[i][0]}"></td>
        <td><input type="number" class="alloc-input mono" data-row="${i}" data-col="1" value="${alloc[i][1]}"></td>
        <td><input type="number" class="alloc-input mono" data-row="${i}" data-col="2" value="${alloc[i][2]}"></td>
      `;
      this.allocTable.appendChild(tr);
    }

    // Build Max Table
    this.maxTable.innerHTML = "";
    for (let i = 0; i < 5; i++) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color: var(--text-muted);">P${i}</td>
        <td><input type="number" class="max-input mono" data-row="${i}" data-col="0" value="${max[i][0]}"></td>
        <td><input type="number" class="max-input mono" data-row="${i}" data-col="1" value="${max[i][1]}"></td>
        <td><input type="number" class="max-input mono" data-row="${i}" data-col="2" value="${max[i][2]}"></td>
      `;
      this.maxTable.appendChild(tr);
    }
  }

  async runBankersSafety() {
    const avail = [
      parseInt(document.getElementById("avail-0").value, 10) || 0,
      parseInt(document.getElementById("avail-1").value, 10) || 0,
      parseInt(document.getElementById("avail-2").value, 10) || 0
    ];

    const alloc = [];
    const max = [];

    for (let i = 0; i < 5; i++) {
      alloc.push([
        parseInt(this.allocTable.querySelector(`input[data-row="${i}"][data-col="0"]`).value, 10) || 0,
        parseInt(this.allocTable.querySelector(`input[data-row="${i}"][data-col="1"]`).value, 10) || 0,
        parseInt(this.allocTable.querySelector(`input[data-row="${i}"][data-col="2"]`).value, 10) || 0
      ]);

      max.push([
        parseInt(this.maxTable.querySelector(`input[data-row="${i}"][data-col="0"]`).value, 10) || 0,
        parseInt(this.maxTable.querySelector(`input[data-row="${i}"][data-col="1"]`).value, 10) || 0,
        parseInt(this.maxTable.querySelector(`input[data-row="${i}"][data-col="2"]`).value, 10) || 0
      ]);
    }

    try {
      const res = await fetch("/api/concurrency/bankers/safety", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ available: avail, allocation: alloc, max_matrix: max })
      });
      const data = await res.json();

      const badge = document.getElementById("bankers-status-badge");
      const seqText = document.getElementById("bankers-sequence-text");
      const stepsLog = document.getElementById("bankers-steps-log");

      if (data.is_safe) {
        badge.className = "badge badge-running";
        badge.textContent = "SAFE STATE: No Deadlock";
        seqText.style.color = "var(--accent-emerald)";
        seqText.textContent = `Safe Sequence: < ${data.safe_sequence_str} >`;
      } else {
        badge.className = "badge badge-zombie";
        badge.textContent = "UNSAFE STATE: Deadlock Risk!";
        seqText.style.color = "var(--accent-rose)";
        seqText.textContent = `No Safe Sequence! Deadlock: ${data.deadlocked_processes.join(", ")}`;
      }

      stepsLog.innerHTML = "";
      (data.steps || []).forEach(st => {
        const d = document.createElement("div");
        d.innerHTML = `<span style="color: var(--accent-cyan);">[Step ${st.step}]</span> ${st.action}`;
        stepsLog.appendChild(d);
      });

      window.app.showToast(data.is_safe ? "Safe sequence found!" : "Deadlock detected!", data.is_safe ? "success" : "error");
    } catch (e) {
      window.app.showToast("Failed to run Banker's check", "error");
    }
  }

  initSync() {
    // Producer-Consumer
    document.getElementById("btn-run-producer-consumer").addEventListener("click", async () => {
      try {
        const res = await fetch("/api/concurrency/producer_consumer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ producers: 2, consumers: 2, capacity: 6, ops: 4 })
        });
        const data = await res.json();

        document.getElementById("pc-produced-count").textContent = data.total_produced;
        document.getElementById("pc-consumed-count").textContent = data.total_consumed;

        // Render buffer slots
        const slotDisplay = document.getElementById("buffer-slot-display");
        slotDisplay.innerHTML = "";
        for (let i = 0; i < 6; i++) {
          const slot = document.createElement("div");
          const hasItem = i < data.final_buffer.length;
          slot.style.flex = "1";
          slot.style.height = "38px";
          slot.style.borderRadius = "6px";
          slot.style.border = "1px solid var(--border-color)";
          slot.style.background = hasItem ? "var(--gradient-accent)" : "rgba(255,255,255,0.03)";
          slot.style.display = "flex";
          slot.style.alignItems = "center";
          slot.style.justifyContent = "center";
          slot.style.fontSize = "0.7rem";
          slot.style.color = hasItem ? "#0a0e17" : "var(--text-muted)";
          slot.style.fontWeight = "600";
          slot.textContent = hasItem ? data.final_buffer[i] : `Slot ${i+1}`;
          slotDisplay.appendChild(slot);
        }

        const logContainer = document.getElementById("pc-events-log");
        logContainer.innerHTML = "";
        data.events.slice(-15).forEach(e => {
          const div = document.createElement("div");
          div.innerHTML = `<span style="color: ${e.actor.startsWith('Producer') ? 'var(--accent-emerald)' : 'var(--accent-purple)'};">[${e.actor}]</span> ${e.action} (Buffer: ${e.buffer_size}/6)`;
          logContainer.appendChild(div);
        });

        window.app.showToast("Producer-Consumer synchronization finished.", "success");
      } catch (e) {
        window.app.showToast("Sync test failed", "error");
      }
    });

    // Readers-Writers
    document.getElementById("btn-run-rw-test").addEventListener("click", async () => {
      try {
        const res = await fetch("/api/concurrency/readers_writers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ readers: 4, writers: 2, iterations: 2 })
        });
        const data = await res.json();

        const logContainer = document.getElementById("rw-events-log");
        logContainer.innerHTML = "";
        data.events.slice(-15).forEach(e => {
          const div = document.createElement("div");
          const isWriter = e.actor.startsWith("Writer");
          div.innerHTML = `<span style="color: ${isWriter ? 'var(--accent-rose)' : 'var(--accent-cyan)'};">[${e.actor}]</span> ${e.action}`;
          logContainer.appendChild(div);
        });

        window.app.showToast("Readers-Writers test finished.", "success");
      } catch (e) {
        window.app.showToast("RW test failed", "error");
      }
    });
  }

  initIPC() {
    document.getElementById("btn-run-ipc-bench").addEventListener("click", async () => {
      const tbody = document.getElementById("ipc-table-body");
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Executing high-precision IPC latency &amp; throughput tests...</td></tr>`;

      try {
        const res = await fetch("/api/concurrency/ipc_benchmark");
        const data = await res.json();
        tbody.innerHTML = "";

        data.benchmark_results.forEach(r => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="mono"><strong>${r.size_kb} KB</strong></td>
            <td class="mono" style="color: var(--accent-emerald); font-weight: 700;">${r.shared_memory.latency_us} μs</td>
            <td class="mono" style="color: var(--accent-emerald); font-weight: 700;">${r.shared_memory.throughput_mb_s} MB/s</td>
            <td class="mono">${r.pipe.latency_us} μs</td>
            <td class="mono">${r.pipe.throughput_mb_s} MB/s</td>
            <td class="mono">${r.message_queue.latency_us} μs</td>
            <td class="mono">${r.message_queue.throughput_mb_s} MB/s</td>
          `;
          tbody.appendChild(tr);
        });

        window.app.showToast("IPC benchmark completed!", "success");
      } catch (e) {
        window.app.showToast("IPC benchmark failed", "error");
      }
    });
  }
}

window.concurrencyView = new ConcurrencyView();
