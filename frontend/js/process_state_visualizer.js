/**
 * Process State Visualizer.
 * Shows CPU execution, ready queue, and process lifecycle states.
 */

class ProcessStateVisualizer {
  constructor() {
    this.cpuContainer = document.getElementById("cpu-viz-container");
    this.readyQueueContainer = document.getElementById("ready-queue-viz");
    this.processStatesContainer = document.getElementById("process-states-viz");
    this.eventLogContainer = document.getElementById("event-log-container");

    // Verify all required elements exist
    if (!this.cpuContainer) {
      console.error("Missing element: cpu-viz-container");
    }
    if (!this.readyQueueContainer) {
      console.error("Missing element: ready-queue-viz");
    }
    if (!this.processStatesContainer) {
      console.error("Missing element: process-states-viz");
    }
    if (!this.eventLogContainer) {
      console.error("Missing element: event-log-container");
    }

    this.runningPid = null;
    this.readyQueue = [];
    this.completedPids = [];
    this.processStates = {}; // pid -> state
    this.eventLog = [];

    this.palette = [
      "#00f2fe", "#4facfe", "#b388ff", "#00e676", "#ffab00",
      "#ff1744", "#ff4081", "#7c4dff", "#00b0ff", "#1de9b6"
    ];
  }

  reset() {
    this.runningPid = null;
    this.readyQueue = [];
    this.completedPids = [];
    this.processStates = {};
    this.eventLog = [];
    this.render();
  }

  onEvent(event) {
    const eventType = event.event;

    // Update process states
    if (eventType === "PROCESS_ARRIVED") {
      this.processStates[event.pid] = "NEW";
      this.addEventLog(event.time, `P${event.pid} arrived`);
    }

    if (eventType === "PROCESS_QUEUED" || eventType === "PROCESS_ARRIVED") {
      this.processStates[event.pid] = "READY";
      if (event.ready_queue) {
        this.readyQueue = event.ready_queue;
      }
    }

    if (eventType === "PROCESS_STARTED" || eventType === "PROCESS_RESUMED") {
      this.processStates[event.pid] = "RUNNING";
      this.runningPid = event.pid;
      if (event.ready_queue) {
        this.readyQueue = event.ready_queue;
      }
      this.addEventLog(event.time, `CPU assigned to P${event.pid}`, event.decision_rationale);
    }

    if (eventType === "PROCESS_PREEMPTED" || eventType === "TIME_QUANTUM_EXPIRED") {
      if (this.runningPid) {
        this.processStates[this.runningPid] = "READY";
      }
      this.runningPid = null;
      this.addEventLog(event.time, `P${event.pid} preempted`, event.decision_rationale);
    }

    if (eventType === "PROCESS_COMPLETED") {
      this.processStates[event.pid] = "TERMINATED";
      this.completedPids.push(event.pid);
      this.runningPid = null;
      if (event.ready_queue) {
        this.readyQueue = event.ready_queue;
      }
      this.addEventLog(event.time, `P${event.pid} completed`, event.decision_rationale);
    }

    if (eventType === "CPU_IDLE") {
      this.runningPid = null;
      this.addEventLog(event.time, "CPU idle");
    }

    if (eventType === "CONTEXT_SWITCH") {
      this.addEventLog(event.time, "Context switch");
    }

    if (eventType === "PRIORITY_CHANGED") {
      this.addEventLog(event.time, `P${event.pid} priority changed`, event.decision_rationale);
    }

    if (eventType === "QUEUE_CHANGED") {
      this.addEventLog(event.time, `P${event.pid} moved to ${event.new_queue}`, event.decision_rationale);
    }

    // Update visuals
    this.render();
  }

  render() {
    this.renderCPU();
    this.renderReadyQueue();
    this.renderProcessStates();
  }

  renderCPU() {
    if (!this.cpuContainer) {
      console.warn("CPU container not found, skipping render");
      return;
    }

    if (this.runningPid === null) {
      this.cpuContainer.innerHTML = `
        <div class="cpu-core idle">
          <div class="cpu-header">CPU CORE</div>
          <div class="cpu-status">IDLE</div>
          <div class="cpu-detail">No process executing</div>
        </div>
      `;
    } else {
      const colorIdx = (this.runningPid * 2) % this.palette.length;
      this.cpuContainer.innerHTML = `
        <div class="cpu-core running" style="border-color: ${this.palette[colorIdx]};">
          <div class="cpu-header">CPU CORE</div>
          <div class="cpu-status" style="color: ${this.palette[colorIdx]};">RUNNING</div>
          <div class="cpu-process">P${this.runningPid}</div>
          <div class="cpu-detail">Executing</div>
        </div>
      `;
    }
  }

  renderReadyQueue() {
    if (!this.readyQueueContainer) {
      console.warn("Ready queue container not found, skipping render");
      return;
    }

    if (!this.readyQueue || this.readyQueue.length === 0) {
      this.readyQueueContainer.innerHTML = `
        <div class="ready-queue-header">READY QUEUE</div>
        <div class="ready-queue-empty">Queue is empty</div>
      `;
      return;
    }

    let queueHTML = '<div class="ready-queue-header">READY QUEUE</div><div class="ready-queue-items">';

    this.readyQueue.forEach((pid, idx) => {
      const colorIdx = (pid * 2) % this.palette.length;
      queueHTML += `
        <div class="ready-queue-item" style="border-color: ${this.palette[colorIdx]};">
          <span class="rq-pid">P${pid}</span>
        </div>
      `;
      if (idx < this.readyQueue.length - 1) {
        queueHTML += '<span class="rq-arrow">→</span>';
      }
    });

    queueHTML += '</div>';
    this.readyQueueContainer.innerHTML = queueHTML;
  }

  renderProcessStates() {
    if (!this.processStatesContainer) {
      console.warn("Process states container not found, skipping render");
      return;
    }

    const pids = Object.keys(this.processStates).map(Number).sort((a, b) => a - b);

    if (pids.length === 0) {
      this.processStatesContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">No processes yet</div>';
      return;
    }

    let statesHTML = '<div class="process-states-grid">';

    pids.forEach(pid => {
      const state = this.processStates[pid];
      const colorIdx = (pid * 2) % this.palette.length;
      let stateClass = "state-new";
      let stateColor = "var(--text-muted)";

      if (state === "READY") {
        stateClass = "state-ready";
        stateColor = "var(--accent-cyan)";
      } else if (state === "RUNNING") {
        stateClass = "state-running";
        stateColor = "var(--accent-emerald)";
      } else if (state === "TERMINATED") {
        stateClass = "state-terminated";
        stateColor = "var(--text-secondary)";
      }

      statesHTML += `
        <div class="process-state-card ${stateClass}">
          <div class="ps-pid" style="color: ${this.palette[colorIdx]};">P${pid}</div>
          <div class="ps-state" style="color: ${stateColor};">${state}</div>
        </div>
      `;
    });

    statesHTML += '</div>';
    this.processStatesContainer.innerHTML = statesHTML;
  }

  addEventLog(time, message, rationale = null) {
    const logEntry = {
      time: time.toFixed(1),
      message: message,
      rationale: rationale
    };

    this.eventLog.push(logEntry);

    // Keep only last 50 events
    if (this.eventLog.length > 50) {
      this.eventLog.shift();
    }

    if (!this.eventLogContainer) {
      console.warn("Event log container not found, skipping log entry");
      return;
    }

    const logItem = document.createElement("div");
    logItem.className = "event-log-item";
    logItem.innerHTML = `
      <span class="log-time">[${logEntry.time}]</span>
      <span class="log-message">${logEntry.message}</span>
    `;

    if (rationale) {
      logItem.title = rationale;
    }

    this.eventLogContainer.appendChild(logItem);

    // Auto-scroll to bottom
    this.eventLogContainer.scrollTop = this.eventLogContainer.scrollHeight;
  }
}

window.processStateVisualizer = null;
