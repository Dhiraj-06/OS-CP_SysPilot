/**
 * Real-Time Simulation Controller.
 * Manages streaming scheduler simulation with playback controls.
 */

class SimulationController {
  constructor() {
    this.ws = null;
    this.state = "IDLE"; // IDLE, RUNNING, PAUSED, COMPLETED
    this.speed = 1.0;
    this.events = [];
    this.currentTime = 0;
    this.processes = [];
    this.algorithm = null;
    this.listeners = [];

    this.initControls();
  }

  initControls() {
    // Play/Pause/Reset/Speed controls
    const btnPlay = document.getElementById("btn-sim-play");
    const btnPause = document.getElementById("btn-sim-pause");
    const btnReset = document.getElementById("btn-sim-reset");
    const btnStep = document.getElementById("btn-sim-step");
    const speedSelect = document.getElementById("sim-speed-select");

    if (btnPlay) {
      btnPlay.addEventListener("click", () => this.play());
    }
    if (btnPause) {
      btnPause.addEventListener("click", () => this.pause());
    }
    if (btnReset) {
      btnReset.addEventListener("click", () => this.reset());
    }
    if (btnStep) {
      btnStep.addEventListener("click", () => this.step());
    }
    if (speedSelect) {
      speedSelect.addEventListener("change", (e) => {
        this.setSpeed(parseFloat(e.target.value));
      });
    }
  }

  subscribe(callback) {
    this.listeners.push(callback);
  }

  dispatch(event) {
    this.listeners.forEach(cb => {
      try {
        cb(event);
      } catch (e) {
        console.error("Simulation event dispatch error:", e);
      }
    });
  }

  async start(algorithm, processes, params = {}) {
    if (this.state === "RUNNING") {
      console.warn("Simulation already running");
      return;
    }

    this.algorithm = algorithm;
    this.processes = processes;
    this.events = [];
    this.currentTime = 0;
    this.state = "RUNNING";

    this.dispatch({
      type: "STATE_CHANGED",
      state: this.state
    });

    // Connect WebSocket
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8001";
    const wsUrl = `${protocol}//${host}/ws/scheduler/simulate`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        // Send simulation request
        this.ws.send(JSON.stringify({
          algorithm: algorithm,
          processes: processes,
          params: params,
          speed: this.speed
        }));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
          console.error("Simulation error:", data.error);
          window.app.showToast("Simulation error: " + data.error, "error");
          this.stop();
          return;
        }

        if (data.event === "SIMULATION_COMPLETE") {
          this.state = "COMPLETED";
          this.dispatch({
            type: "STATE_CHANGED",
            state: this.state
          });
          this.dispatch({
            type: "SIMULATION_COMPLETE",
            makespan: data.makespan
          });
          this.ws.close();
          return;
        }

        // Store and dispatch event
        this.events.push(data);
        this.currentTime = data.time;

        this.dispatch({
          type: "SIMULATION_EVENT",
          event: data
        });
      };

      this.ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        window.app.showToast("Simulation connection error", "error");
        this.stop();
      };

      this.ws.onclose = () => {
        if (this.state === "RUNNING") {
          this.state = "IDLE";
          this.dispatch({
            type: "STATE_CHANGED",
            state: this.state
          });
        }
      };

    } catch (e) {
      console.error("Failed to start simulation:", e);
      window.app.showToast("Failed to start simulation", "error");
      this.state = "IDLE";
      this.dispatch({
        type: "STATE_CHANGED",
        state: this.state
      });
    }
  }

  play() {
    if (this.state === "PAUSED" && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.state = "RUNNING";
      this.ws.send(JSON.stringify({ action: "resume" }));
      this.dispatch({
        type: "STATE_CHANGED",
        state: this.state
      });
    }
  }

  pause() {
    if (this.state === "RUNNING" && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.state = "PAUSED";
      this.ws.send(JSON.stringify({ action: "pause" }));
      this.dispatch({
        type: "STATE_CHANGED",
        state: this.state
      });
    }
  }

  stop() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "stop" }));
      this.ws.close();
    }
    this.state = "IDLE";
    this.dispatch({
      type: "STATE_CHANGED",
      state: this.state
    });
  }

  reset() {
    this.stop();
    this.events = [];
    this.currentTime = 0;
    this.dispatch({
      type: "SIMULATION_RESET"
    });
  }

  step() {
    // Step forward one event (for future implementation)
    console.log("Step functionality - to be implemented");
  }

  setSpeed(speed) {
    this.speed = speed;
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: "speed",
        value: speed
      }));
    }
    this.dispatch({
      type: "SPEED_CHANGED",
      speed: speed
    });
  }

  getState() {
    return {
      state: this.state,
      currentTime: this.currentTime,
      events: this.events,
      algorithm: this.algorithm
    };
  }
}

window.simulationController = new SimulationController();
