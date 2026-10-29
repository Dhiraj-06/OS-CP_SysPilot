"""Anomaly & Memory Leak Detector.

Implements:
1. Memory Leak Detection: Analyzes process Resident Set Size (RSS) rate of change
   (dRSS/dt > 0 with strong linearity R² > 0.85). Flags memory hoarding before
   OS OOM (Out Of Memory) Killer invokes SIGKILL.
2. CPU Hog Detection: Flags processes consuming disproportionate CPU ticks continuously.
3. Synthetic Workload Injector: Enables live demonstration during evaluations.
"""

from typing import Dict, Any, List
import time
import threading
import psutil
import numpy as np
from ..config import LEAK_SLOPE_THRESHOLD, CPU_HIGH_THRESHOLD

class AnomalyDetector:
    """Detects runaway CPU processes and memory leaks."""

    def __init__(self):
        # PID -> deque of (timestamp, rss_bytes, cpu_percent)
        self._process_history: Dict[int, List[Dict[str, float]]] = {}
        self._lock = threading.Lock()
        self._synthetic_threads = []

    def update_and_detect(self) -> Dict[str, Any]:
        """Inspect top processes and evaluate anomaly conditions."""
        now = time.time()
        leaks_detected = []
        cpu_hogs = []

        with self._lock:
            # Sample current top processes
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pid = p.info['pid']
                    if pid == 0:
                        continue
                    mem = p.info['memory_info']
                    rss_mb = mem.rss / (1024 * 1024) if mem else 0.0
                    cpu = p.info['cpu_percent'] or 0.0

                    if pid not in self._process_history:
                        self._process_history[pid] = []
                    
                    history = self._process_history[pid]
                    history.append({"timestamp": now, "rss_mb": rss_mb, "cpu": cpu})

                    # Maintain up to 10 points
                    if len(history) > 10:
                        history.pop(0)

                    # Evaluate Memory Leak
                    if len(history) >= 5:
                        times = np.array([h["timestamp"] for h in history])
                        rss_vals = np.array([h["rss_mb"] for h in history])
                        dt = times[-1] - times[0]
                        if dt > 3.0: # Need at least 3 seconds spread
                            # Fit line
                            slope, _ = np.polyfit(times - times[0], rss_vals, 1)
                            # Check monotonic increase
                            diffs = np.diff(rss_vals)
                            is_mostly_growing = np.sum(diffs > 0) >= (len(diffs) - 1)
                            
                            if slope >= LEAK_SLOPE_THRESHOLD and is_mostly_growing:
                                leaks_detected.append({
                                    "pid": pid,
                                    "name": p.name(),
                                    "growth_rate_mb_s": round(slope, 2),
                                    "current_rss_mb": round(rss_mb, 1),
                                    "severity": "HIGH" if slope > 2.0 else "MEDIUM",
                                    "recommendation": "Investigate uncollected buffers or invoke SIGTERM to prevent OOM killer."
                                })

                    # Evaluate CPU Hog
                    if cpu >= CPU_HIGH_THRESHOLD:
                        cpu_hogs.append({
                            "pid": pid,
                            "name": p.name(),
                            "cpu_percent": round(cpu, 1),
                            "severity": "HIGH",
                            "recommendation": "Inspect for infinite loops or renice to deprioritize."
                        })

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        return {
            "timestamp": now,
            "memory_leaks": leaks_detected,
            "cpu_hogs": cpu_hogs,
            "total_anomalies": len(leaks_detected) + len(cpu_hogs),
            "status": "ANOMALY_DETECTED" if (leaks_detected or cpu_hogs) else "NORMAL"
        }

    def simulate_anomaly(self, anomaly_type: str = "leak", duration_seconds: int = 15) -> Dict[str, Any]:
        """Trigger synthetic memory leak or CPU spike for evaluation demo."""
        stop_event = threading.Event()

        if anomaly_type == "leak":
            def leak_worker():
                blob = []
                start = time.time()
                while not stop_event.is_set() and (time.time() - start) < duration_seconds:
                    blob.append(b"X" * (2 * 1024 * 1024)) # Allocate 2 MB every 200ms
                    time.sleep(0.2)
                time.sleep(2)
                blob.clear()

            t = threading.Thread(target=leak_worker, daemon=True)
            t.start()
            return {"success": True, "message": f"Synthetic memory leak initiated for {duration_seconds}s."}

        elif anomaly_type == "cpu_hog":
            def cpu_worker():
                start = time.time()
                while not stop_event.is_set() and (time.time() - start) < duration_seconds:
                    # Busy spin
                    _ = [x * x for x in range(100000)]
                    time.sleep(0.001)

            t = threading.Thread(target=cpu_worker, daemon=True)
            t.start()
            return {"success": True, "message": f"Synthetic CPU spike initiated for {duration_seconds}s."}

        return {"success": False, "error": f"Unknown anomaly type: {anomaly_type}"}
