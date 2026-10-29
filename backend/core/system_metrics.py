"""System Metrics Service: Aggregates real-time hardware & kernel metrics.

Collects and computes:
- Aggregate CPU load & per-core CPU load percentages
- Virtual Memory breakdown (Total, Used, Available, Buffers, Cached)
- Swap Space consumption
- Disk usage & I/O read/write throughput (KB/s)
- Network throughput (RX / TX KB/s)
- System uptime, context switches, interrupt rates
"""

import time
import psutil
from .proc_parser import ProcParser

class SystemMetricsService:
    """Collects real-time system performance telemetry."""

    def __init__(self):
        self.proc_parser = ProcParser()
        self._last_time = time.time()
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        # Prime cpu_percent
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

    def get_snapshot(self) -> dict:
        """Capture an instantaneous, consolidated system metric snapshot."""
        now = time.time()
        dt = max(now - self._last_time, 0.001)

        # CPU via proc_parser delta calculation (procfs on Linux, psutil on Windows)
        cpu_metrics = self.proc_parser.get_cpu_percentages()
        total_cpu = cpu_metrics["aggregate_percent"]
        per_core_cpu = cpu_metrics["per_core_percent"]
        cpu_count_logical = psutil.cpu_count(logical=True) or 1
        cpu_count_physical = psutil.cpu_count(logical=False) or 1

        # Memory from proc_parser
        mem_info = self.proc_parser.parse_meminfo()

        # Disk I/O delta
        current_disk_io = psutil.disk_io_counters()
        read_bytes_sec = 0.0
        write_bytes_sec = 0.0
        if current_disk_io and self._last_disk_io:
            read_bytes_sec = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / dt
            write_bytes_sec = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / dt
        self._last_disk_io = current_disk_io

        # Network I/O delta
        current_net_io = psutil.net_io_counters()
        rx_bytes_sec = 0.0
        tx_bytes_sec = 0.0
        if current_net_io and self._last_net_io:
            rx_bytes_sec = (current_net_io.bytes_recv - self._last_net_io.bytes_recv) / dt
            tx_bytes_sec = (current_net_io.bytes_sent - self._last_net_io.bytes_sent) / dt
        self._last_net_io = current_net_io

        self._last_time = now

        # Disk storage
        try:
            disk_usage = psutil.disk_usage('/')
            disk_total = disk_usage.total
            disk_used = disk_usage.used
            disk_percent = disk_usage.percent
        except Exception:
            disk_usage = psutil.disk_usage('C:\\')
            disk_total = disk_usage.total
            disk_used = disk_usage.used
            disk_percent = disk_usage.percent

        # Load average
        load_avg = self.proc_parser.parse_loadavg()

        # OS boot time & uptime
        boot_time = psutil.boot_time()
        uptime_seconds = int(now - boot_time)

        return {
            "timestamp": now,
            "cpu": {
                "aggregate_percent": round(total_cpu, 1),
                "per_core_percent": [round(c, 1) for c in per_core_cpu],
                "physical_cores": cpu_count_physical,
                "logical_cores": cpu_count_logical
            },
            "memory": {
                "total": mem_info["total"],
                "available": mem_info["available"],
                "used": mem_info["used"],
                "free": mem_info["free"],
                "buffers": mem_info["buffers"],
                "cached": mem_info["cached"],
                "percent": mem_info["percent"],
                "swap_total": mem_info["swap_total"],
                "swap_used": mem_info["swap_used"],
                "swap_percent": mem_info["swap_percent"]
            },
            "disk": {
                "total": disk_total,
                "used": disk_used,
                "percent": disk_percent,
                "read_kb_s": round(read_bytes_sec / 1024.0, 1),
                "write_kb_s": round(write_bytes_sec / 1024.0, 1)
            },
            "network": {
                "rx_kb_s": round(rx_bytes_sec / 1024.0, 1),
                "tx_kb_s": round(tx_bytes_sec / 1024.0, 1)
            },
            "system": {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "load": load_avg,
                "total_processes": len(psutil.pids())
            }
        }

    def _format_uptime(self, seconds: int) -> str:
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m {secs}s"
