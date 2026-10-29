"""Ring Buffer for System Telemetry Data.

Stores sliding-window historical metrics for ML training and online forecasting.
"""

from collections import deque
import threading
import time
from typing import Dict, Any, List, Tuple
import numpy as np

class TelemetryBuffer:
    """Thread-safe circular buffer for time-series metrics."""

    def __init__(self, maxlen: int = 120):
        self.buffer = deque(maxlen=maxlen)
        self.lock = threading.Lock()

    def append(self, snapshot: Dict[str, Any]):
        """Record a single timestamped telemetry snapshot."""
        with self.lock:
            entry = {
                "timestamp": snapshot.get("timestamp", time.time()),
                "cpu_percent": snapshot.get("cpu", {}).get("aggregate_percent", 0.0),
                "mem_percent": snapshot.get("memory", {}).get("percent", 0.0),
                "mem_used_mb": snapshot.get("memory", {}).get("used", 0) / (1024 * 1024),
                "swap_percent": snapshot.get("memory", {}).get("swap_percent", 0.0),
                "disk_read_kb_s": snapshot.get("disk", {}).get("read_kb_s", 0.0),
                "disk_write_kb_s": snapshot.get("disk", {}).get("write_kb_s", 0.0),
                "net_rx_kb_s": snapshot.get("network", {}).get("rx_kb_s", 0.0),
                "net_tx_kb_s": snapshot.get("network", {}).get("tx_kb_s", 0.0),
                "total_procs": snapshot.get("system", {}).get("total_processes", 0)
            }
            self.buffer.append(entry)

    def get_history(self, count: int = 60) -> List[Dict[str, Any]]:
        """Retrieve the most recent N telemetry points."""
        with self.lock:
            items = list(self.buffer)
            return items[-count:]

    def get_feature_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract timestamps, CPU series, and RAM series as NumPy arrays."""
        with self.lock:
            if len(self.buffer) < 5:
                # Synthesize baseline if newly started
                t_now = time.time()
                times = np.arange(-10, 0, 1.0)
                cpu = np.array([20.0 + np.sin(i) * 5.0 for i in range(10)])
                mem = np.array([45.0 + np.cos(i) * 2.0 for i in range(10)])
                return times, cpu, mem

            times = np.array([item["timestamp"] for item in self.buffer])
            cpu = np.array([item["cpu_percent"] for item in self.buffer])
            mem = np.array([item["mem_percent"] for item in self.buffer])
            return times, cpu, mem
