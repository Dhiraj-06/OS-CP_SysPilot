/**
 * Machine Learning Forecasting & Anomaly Center View.
 * Handles future resource projections (+10s, +30s, +60s),
 * model R² metrics, memory leak detection, and synthetic workload simulation.
 */

class MLView {
  constructor() {
    this.initListeners();

    // Subscribe to telemetry WebSocket ticks
    window.telemetryWs.subscribe((data) => {
      if (data.forecast) {
        this.renderForecast(data.forecast);
      }
      if (data.anomalies) {
        this.renderAnomalies(data.anomalies);
      }
    });
  }

  initListeners() {
    document.getElementById("btn-sim-leak").addEventListener("click", () => this.simulateAnomaly("leak"));
    document.getElementById("btn-sim-cpu-hog").addEventListener("click", () => this.simulateAnomaly("cpu_hog"));
  }

  renderForecast(fc) {
    if (!fc || !fc.predictions) return;

    // +10s
    if (fc.predictions[0]) {
      const p10 = fc.predictions[0];
      document.getElementById("forecast-cpu-10").textContent = `${p10.predicted_cpu_percent}%`;
      document.getElementById("forecast-mem-10").textContent = `${p10.predicted_mem_percent}%`;
      document.getElementById("delta-cpu-10").textContent = `${p10.cpu_delta >= 0 ? '+' : ''}${p10.cpu_delta}%`;
      document.getElementById("delta-mem-10").textContent = `${p10.mem_delta >= 0 ? '+' : ''}${p10.mem_delta}%`;
    }

    // +30s
    if (fc.predictions[1]) {
      const p30 = fc.predictions[1];
      document.getElementById("forecast-cpu-30").textContent = `${p30.predicted_cpu_percent}%`;
      document.getElementById("forecast-mem-30").textContent = `${p30.predicted_mem_percent}%`;
      document.getElementById("delta-cpu-30").textContent = `${p30.cpu_delta >= 0 ? '+' : ''}${p30.cpu_delta}%`;
      document.getElementById("delta-mem-30").textContent = `${p30.mem_delta >= 0 ? '+' : ''}${p30.mem_delta}%`;
    }

    // +60s
    if (fc.predictions[2]) {
      const p60 = fc.predictions[2];
      document.getElementById("forecast-cpu-60").textContent = `${p60.predicted_cpu_percent}%`;
      document.getElementById("forecast-mem-60").textContent = `${p60.predicted_mem_percent}%`;
      document.getElementById("delta-cpu-60").textContent = `${p60.cpu_delta >= 0 ? '+' : ''}${p60.cpu_delta}%`;
      document.getElementById("delta-mem-60").textContent = `${p60.mem_delta >= 0 ? '+' : ''}${p60.mem_delta}%`;
    }

    // Trend details
    document.getElementById("ml-cpu-trend").textContent = fc.cpu_trend;
    document.getElementById("ml-cpu-slope").textContent = `${fc.cpu_slope_per_sec >= 0 ? '+' : ''}${fc.cpu_slope_per_sec}`;
    document.getElementById("ml-mem-trend").textContent = fc.mem_trend;
    document.getElementById("ml-mem-slope").textContent = `${fc.mem_slope_per_sec >= 0 ? '+' : ''}${fc.mem_slope_per_sec}`;

    if (fc.confidence_r2) {
      document.getElementById("ml-r2-cpu").textContent = fc.confidence_r2.cpu.toFixed(2);
      document.getElementById("ml-r2-mem").textContent = fc.confidence_r2.mem.toFixed(2);
    }
  }

  renderAnomalies(anom) {
    const container = document.getElementById("anomaly-alerts-container");
    const badge = document.getElementById("anomaly-status-badge");

    if (!anom || anom.total_anomalies === 0) {
      badge.className = "badge badge-running";
      badge.textContent = "NORMAL";
      container.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted);">No anomalies currently detected. System running within normal parameters.</div>`;
      return;
    }

    badge.className = "badge badge-zombie";
    badge.textContent = `${anom.total_anomalies} ANOMALY DETECTED`;
    container.innerHTML = "";

    // Memory leaks
    (anom.memory_leaks || []).forEach(leak => {
      const card = document.createElement("div");
      card.style.padding = "0.75rem";
      card.style.borderRadius = "var(--radius-sm)";
      card.style.background = "rgba(255, 23, 68, 0.15)";
      card.style.border = "1px solid rgba(255, 23, 68, 0.4)";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: var(--accent-rose);">⚠️ Memory Leak: ${leak.name} (PID: ${leak.pid})</strong>
          <span class="badge badge-zombie mono">+${leak.growth_rate_mb_s} MB/s</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.3rem;">
          Current RSS: ${leak.current_rss_mb} MB | Rate: dRSS/dt = +${leak.growth_rate_mb_s} MB/sec.
        </div>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">
          ${leak.recommendation}
        </div>
      `;
      container.appendChild(card);
    });

    // CPU hogs
    (anom.cpu_hogs || []).forEach(hog => {
      const card = document.createElement("div");
      card.style.padding = "0.75rem";
      card.style.borderRadius = "var(--radius-sm)";
      card.style.background = "rgba(255, 171, 0, 0.15)";
      card.style.border = "1px solid rgba(255, 171, 0, 0.4)";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: var(--accent-amber);">🔥 High CPU Spike: ${hog.name} (PID: ${hog.pid})</strong>
          <span class="badge badge-stopped mono">${hog.cpu_percent}% CPU</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.3rem;">
          ${hog.recommendation}
        </div>
      `;
      container.appendChild(card);
    });
  }

  async simulateAnomaly(type) {
    try {
      const res = await fetch("/api/ml/simulate_anomaly", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anomaly_type: type, duration_seconds: 15 })
      });
      const data = await res.json();
      window.app.showToast(data.message || "Anomaly simulation initiated!", "info");
    } catch (e) {
      window.app.showToast("Failed to start synthetic anomaly", "error");
    }
  }
}

window.mlView = new MLView();
