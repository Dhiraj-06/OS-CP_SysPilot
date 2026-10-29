/**
 * Multi-Client Concurrent File Service View.
 * Tracks OS Page Cache (LRU), active reader/writer locks,
 * manual client I/O console, and automated stress testing.
 */

class FileServiceView {
  constructor() {
    this.initListeners();
    this.fetchStatus();
  }

  initListeners() {
    document.getElementById("btn-refresh-file-status").addEventListener("click", () => this.fetchStatus());
    document.getElementById("btn-launch-stress-test").addEventListener("click", () => this.runStressTest());

    // Manual client actions
    document.getElementById("btn-manual-read").addEventListener("click", () => this.doManualOp("READ"));
    document.getElementById("btn-manual-write").addEventListener("click", () => this.doManualOp("WRITE"));
    document.getElementById("btn-manual-append").addEventListener("click", () => this.doManualOp("APPEND"));
  }

  async fetchStatus() {
    try {
      const res = await fetch("/api/file_service/status");
      const data = await res.json();
      this.renderStatus(data);
    } catch (e) {
      console.error("Failed to fetch file service status:", e);
    }
  }

  renderStatus(data) {
    const cache = data.cache_stats;
    document.getElementById("cache-hit-ratio-badge").textContent = `Hit Ratio: ${cache.hit_ratio_percent}%`;
    document.getElementById("cache-hits-val").textContent = cache.hits;
    document.getElementById("cache-misses-val").textContent = cache.misses;
    document.getElementById("cache-evictions-val").textContent = cache.evictions;

    // Render cached pages table
    const pageBody = document.getElementById("cached-pages-body");
    pageBody.innerHTML = "";

    if (!cache.cached_pages || cache.cached_pages.length === 0) {
      pageBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Cache empty.</td></tr>`;
    } else {
      cache.cached_pages.forEach(p => {
        const tr = document.createElement("tr");
        const dirtyBadge = p.dirty
          ? `<span class="badge badge-zombie">DIRTY (Unflushed)</span>`
          : `<span class="badge badge-running">CLEAN</span>`;
        tr.innerHTML = `
          <td><strong>${p.filename}</strong></td>
          <td>${dirtyBadge}</td>
          <td class="mono">${p.size_bytes} B</td>
          <td class="mono" style="color: var(--text-muted);">${p.last_accessed}</td>
        `;
        pageBody.appendChild(tr);
      });
    }

    // Render activity stream
    const actBody = document.getElementById("file-activity-body");
    actBody.innerHTML = "";

    if (!data.recent_activity || data.recent_activity.length === 0) {
      actBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No client activity recorded yet.</td></tr>`;
    } else {
      data.recent_activity.forEach(a => {
        const tr = document.createElement("tr");
        let opColor = "var(--accent-cyan)";
        if (a.operation === "WRITE") opColor = "var(--accent-rose)";
        else if (a.operation === "APPEND") opColor = "var(--accent-amber)";

        tr.innerHTML = `
          <td class="mono" style="color: var(--text-muted);">${a.timestamp}</td>
          <td><strong style="color: var(--accent-blue);">${a.client_id}</strong></td>
          <td><span class="mono" style="color: ${opColor}; font-weight: 700;">${a.operation}</span></td>
          <td class="mono">${a.filename}</td>
          <td class="mono">${a.latency_ms} ms</td>
          <td style="color: var(--text-secondary); font-size: 0.8rem;">${a.details}</td>
        `;
        actBody.appendChild(tr);
      });
    }
  }

  async doManualOp(opType) {
    const clientId = document.getElementById("manual-client-id").value.trim() || "Client_User";
    const filename = document.getElementById("manual-filename").value.trim() || "test.txt";
    const content = document.getElementById("manual-file-content").value;
    const resBox = document.getElementById("manual-op-result");

    resBox.textContent = `Executing concurrent ${opType}...`;

    try {
      let endpoint = "/api/file_service/read";
      let payload = { client_id: clientId, filename: filename };

      if (opType === "WRITE") {
        endpoint = "/api/file_service/write";
        payload.content = content;
      } else if (opType === "APPEND") {
        endpoint = "/api/file_service/append";
        payload.content = content;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (opType === "READ") {
        resBox.innerHTML = `<span style="color: var(--accent-emerald);">Success (${data.source}):</span> Content: "${data.content.slice(0, 80)}" [${data.latency_ms} ms]`;
        document.getElementById("manual-file-content").value = data.content;
      } else {
        resBox.innerHTML = `<span style="color: var(--accent-emerald);">Success:</span> Mutex write lock acquired & released. [${data.latency_ms} ms]`;
      }

      this.fetchStatus();
      window.app.showToast(`${opType} operation complete.`, "success");
    } catch (e) {
      resBox.textContent = `Operation error: ${e.message}`;
    }
  }

  async runStressTest() {
    const numClients = parseInt(document.getElementById("stress-clients-input").value, 10) || 5;
    const opsPerClient = parseInt(document.getElementById("stress-ops-input").value, 10) || 6;
    const resultBox = document.getElementById("stress-test-result-box");

    resultBox.style.display = "block";
    resultBox.innerHTML = `Spawning <strong>${numClients}</strong> concurrent threads firing <strong>${opsPerClient}</strong> I/O operations each...`;

    try {
      const res = await fetch("/api/file_service/stress_test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_clients: numClients, operations_per_client: opsPerClient })
      });
      const data = await res.json();

      resultBox.innerHTML = `
        <div style="color: var(--accent-emerald); font-weight: 700; margin-bottom: 0.3rem;">✓ Concurrent Stress Test Finished!</div>
        <div>Completed <strong>${data.total_operations}</strong> operations across <strong>${data.num_clients}</strong> clients in <strong>${data.duration_seconds}s</strong>.</div>
        <div>Throughput: <strong class="mono" style="color: var(--accent-cyan);">${data.throughput_ops_sec} ops/sec</strong> (Errors: ${data.errors_count})</div>
      `;

      if (data.server_status) {
        this.renderStatus(data.server_status);
      } else {
        this.fetchStatus();
      }

      window.app.showToast("Stress test finished successfully!", "success");
    } catch (e) {
      resultBox.textContent = `Stress test failed: ${e.message}`;
    }
  }
}

window.fileServiceView = new FileServiceView();
