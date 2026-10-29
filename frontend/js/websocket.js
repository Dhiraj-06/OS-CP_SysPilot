/**
 * WebSocket Telemetry Manager for SysPilot.
 * Maintains real-time bi-directional telemetry connection and dispatches data.
 */

class TelemetryWebSocket {
  constructor() {
    this.ws = null;
    this.reconnectInterval = 3000;
    this.indicator = document.getElementById("ws-indicator");
    this.statusText = document.getElementById("ws-status-text");
    this.subscribers = [];
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `${protocol}//${host}/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        if (this.indicator) {
          this.indicator.classList.remove("offline");
          this.statusText.textContent = "Live Telemetry Active";
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.dispatch(payload);
        } catch (e) {
          console.error("WS Parse error:", e);
        }
      };

      this.ws.onclose = () => {
        if (this.indicator) {
          this.indicator.classList.add("offline");
          this.statusText.textContent = "Offline (Reconnecting...)";
        }
        setTimeout(() => this.connect(), this.reconnectInterval);
      };

      this.ws.onerror = (err) => {
        if (this.indicator) {
          this.indicator.classList.add("offline");
        }
      };
    } catch (e) {
      console.warn("WebSocket connection failure:", e);
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  subscribe(callback) {
    this.subscribers.push(callback);
  }

  dispatch(data) {
    // 1. Update Global Quickbar
    if (data.system) {
      this.updateQuickbar(data.system);
    }

    // 2. Pass to all registered view subscribers
    for (const sub of this.subscribers) {
      try {
        sub(data);
      } catch (err) {
        console.error("Subscriber dispatch error:", err);
      }
    }
  }

  updateQuickbar(sys) {
    // CPU
    const cpuVal = sys.cpu.aggregate_percent;
    document.getElementById("quick-cpu-val").textContent = cpuVal.toFixed(1);
    document.getElementById("quick-cpu-bar").style.width = `${Math.min(cpuVal, 100)}%`;
    document.getElementById("cpu-core-count").textContent = `${sys.cpu.logical_cores} Logical Cores`;
    if (sys.system && sys.system.load) {
      const l = sys.system.load;
      document.getElementById("quick-loadavg").textContent = `${l.load1}, ${l.load5}, ${l.load15}`;
    }

    // Memory
    const mem = sys.memory;
    document.getElementById("quick-mem-val").textContent = mem.percent.toFixed(1);
    document.getElementById("quick-mem-bar").style.width = `${mem.percent}%`;
    const usedGb = (mem.used / (1024 ** 3)).toFixed(1);
    const totalGb = (mem.total / (1024 ** 3)).toFixed(1);
    document.getElementById("quick-mem-used").textContent = `${usedGb} / ${totalGb} GB`;
    document.getElementById("quick-mem-cached").textContent = `${(mem.cached / (1024 ** 2)).toFixed(0)} MB`;
    document.getElementById("quick-swap-val").textContent = `${mem.swap_percent.toFixed(1)}%`;

    // Disk
    const disk = sys.disk;
    const diskVal = ((disk.read_kb_s + disk.write_kb_s) / 1024).toFixed(1);
    document.getElementById("quick-disk-val").textContent = diskVal;
    document.getElementById("quick-disk-space").textContent = `${disk.percent}% Used`;
    document.getElementById("quick-disk-bar").style.width = `${disk.percent}%`;
    document.getElementById("quick-disk-read").textContent = `${disk.read_kb_s.toFixed(0)} KB/s`;
    document.getElementById("quick-disk-write").textContent = `${disk.write_kb_s.toFixed(0)} KB/s`;

    // Network
    const net = sys.network;
    const netTotal = ((net.rx_kb_s + net.tx_kb_s) / 1024).toFixed(1);
    document.getElementById("quick-net-val").textContent = netTotal;
    const netPct = Math.min(100, (net.rx_kb_s + net.tx_kb_s) / 50); // Scale relative to 5MB/s
    document.getElementById("quick-net-bar").style.width = `${netPct}%`;
    document.getElementById("quick-net-rx").textContent = `${net.rx_kb_s.toFixed(0)} KB/s`;
    document.getElementById("quick-net-tx").textContent = `${net.tx_kb_s.toFixed(0)} KB/s`;

    // Uptime
    if (sys.system && sys.system.uptime_formatted) {
      document.getElementById("hdr-uptime").textContent = sys.system.uptime_formatted;
      document.getElementById("total-procs-badge").textContent = `Active Procs: ${sys.system.total_processes}`;
    }
  }
}

window.telemetryWs = new TelemetryWebSocket();
