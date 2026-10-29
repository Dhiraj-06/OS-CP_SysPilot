/**
 * Live Gantt Chart Renderer with Progressive Timeline Building.
 * Builds timeline incrementally as simulation events arrive.
 */

class LiveGanttChart {
  constructor(timelineContainerId, ticksContainerId) {
    this.timelineContainer = document.getElementById(timelineContainerId);
    this.ticksContainer = document.getElementById(ticksContainerId);
    this.blocks = [];
    this.currentTime = 0;
    this.makespan = 0;
    this.palette = [
      "#00f2fe", "#4facfe", "#b388ff", "#00e676", "#ffab00",
      "#ff1744", "#ff4081", "#7c4dff", "#00b0ff", "#1de9b6"
    ];
    this.currentBlock = null;
  }

  reset() {
    this.blocks = [];
    this.currentTime = 0;
    this.makespan = 0;
    this.currentBlock = null;
    if (this.timelineContainer) {
      this.timelineContainer.innerHTML = "";
    }
    if (this.ticksContainer) {
      this.ticksContainer.innerHTML = "<span>0</span>";
    }
  }

  onEvent(event) {
    const eventType = event.event;

    if (eventType === "PROCESS_STARTED" || eventType === "PROCESS_RESUMED") {
      this.startBlock(event.pid, event.process, event.time);
    } else if (eventType === "PROCESS_COMPLETED" || eventType === "PROCESS_PREEMPTED" || eventType === "TIME_QUANTUM_EXPIRED") {
      this.endBlock(event.time);
    } else if (eventType === "CPU_IDLE") {
      this.startBlock("IDLE", null, event.time);
    } else if (eventType === "PROCESS_EXECUTING") {
      this.updateCurrentBlock(event.time, event.remaining_burst);
    } else if (eventType === "SIMULATION_COMPLETE") {
      this.makespan = event.makespan;
      this.finalize();
    }
  }

  startBlock(pid, process, time) {
    if (this.currentBlock) {
      this.endBlock(time);
    }

    this.currentBlock = {
      pid: pid,
      name: process ? process.name : "IDLE",
      start: time,
      end: null,
      element: null
    };
  }

  updateCurrentBlock(time, remaining) {
    if (this.currentBlock && !this.currentBlock.element) {
      // Create visual block
      const block = document.createElement("div");
      block.className = "gantt-block live";

      if (this.currentBlock.pid === "IDLE") {
        block.classList.add("idle");
        block.innerHTML = `<span style="font-size: 0.7rem;">IDLE</span>`;
      } else {
        const colorIdx = (this.currentBlock.pid * 2) % this.palette.length;
        block.style.background = this.palette[colorIdx];
        block.style.borderLeft = `3px solid ${this.palette[colorIdx]}`;
        block.innerHTML = `
          <span>${this.currentBlock.name}</span>
          <span class="remaining" style="font-size: 0.68rem; opacity: 0.85;">rem: ${remaining || "?"}</span>
        `;
      }

      this.timelineContainer.appendChild(block);
      this.currentBlock.element = block;
    }

    // Update remaining time display
    if (this.currentBlock && this.currentBlock.element && remaining !== undefined) {
      const remSpan = this.currentBlock.element.querySelector(".remaining");
      if (remSpan) {
        remSpan.textContent = `rem: ${remaining}`;
      }
    }
  }

  endBlock(time) {
    if (this.currentBlock) {
      this.currentBlock.end = time;

      // Finalize block
      if (this.currentBlock.element) {
        this.currentBlock.element.classList.remove("live");
        const duration = this.currentBlock.end - this.currentBlock.start;

        if (this.currentBlock.pid === "IDLE") {
          this.currentBlock.element.innerHTML = `
            <span style="font-size: 0.72rem;">IDLE</span>
            <span style="font-size: 0.65rem;">Δ${duration.toFixed(1)}</span>
          `;
        } else {
          this.currentBlock.element.innerHTML = `
            <span>${this.currentBlock.name}</span>
            <span style="font-size: 0.68rem; opacity: 0.85;">[${this.currentBlock.start} - ${this.currentBlock.end}]</span>
          `;
        }

        this.currentBlock.element.title = `${this.currentBlock.name}: t=${this.currentBlock.start} to t=${this.currentBlock.end} (Duration: ${duration})`;
      }

      this.blocks.push(this.currentBlock);

      // Add tick mark
      if (this.ticksContainer) {
        const tick = document.createElement("span");
        tick.textContent = this.currentBlock.end;
        this.ticksContainer.appendChild(tick);
      }

      this.currentBlock = null;
    }
  }

  finalize() {
    if (this.currentBlock) {
      this.endBlock(this.makespan);
    }

    // Adjust widths based on final makespan
    if (this.makespan > 0 && this.timelineContainer) {
      const blocks = this.timelineContainer.querySelectorAll(".gantt-block");
      blocks.forEach((block, idx) => {
        if (this.blocks[idx]) {
          const duration = this.blocks[idx].end - this.blocks[idx].start;
          const widthPct = (duration / this.makespan) * 100;
          block.style.width = `${widthPct}%`;
        }
      });
    }
  }
}

window.liveGanttChart = null;
