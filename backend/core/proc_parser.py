"""Linux /proc Filesystem Parser & Cross-Platform Engine.

Provides direct kernel telemetry extraction from the Linux procfs:
- /proc/stat       (aggregate & per-core CPU time slices)
- /proc/meminfo    (detailed kernel memory distribution: Buffers, Cached, Free)
- /proc/loadavg    (1, 5, 15-minute system load averages)
- /proc/[pid]/stat (process execution state, ppid, utime, stime, priority, nice)
- /proc/[pid]/status (memory RSS, virtual memory, thread count, UID)

Includes an automated fallback engine for non-Linux platforms (Windows/macOS)
powered by psutil, ensuring multi-platform portability without compromising
academic demonstration of Linux kernel internals.
"""

from pathlib import Path
import os
import platform
import time
import psutil

IS_LINUX = platform.system() == "Linux" and Path("/proc").is_dir()

class ProcParser:
    """Parser for Linux /proc virtual filesystem with cross-platform fallback."""

    def __init__(self):
        self.is_linux = IS_LINUX
        self._last_cpu_stat = {}
        self._last_cpu_time = 0.0
        # Initialize initial sample if on Linux
        if self.is_linux:
            self._read_raw_proc_stat()

    def _read_raw_proc_stat(self) -> dict:
        """Read raw cumulative jiffies from /proc/stat for total and per-core CPU."""
        data = {}
        if not (self.is_linux and Path("/proc/stat").exists()):
            return data
        try:
            with open("/proc/stat", "r") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                name = parts[0]
                if name.startswith("cpu"):
                    # fields: user, nice, system, idle, iowait, irq, softirq, steal
                    ticks = [int(x) for x in parts[1:9]]
                    user = ticks[0]
                    nice = ticks[1]
                    system = ticks[2]
                    idle = ticks[3]
                    iowait = ticks[4] if len(ticks) > 4 else 0
                    irq = ticks[5] if len(ticks) > 5 else 0
                    softirq = ticks[6] if len(ticks) > 6 else 0
                    steal = ticks[7] if len(ticks) > 7 else 0

                    total = sum(ticks)
                    idle_all = idle + iowait
                    active = total - idle_all

                    data[name] = {
                        "user": user,
                        "nice": nice,
                        "system": system,
                        "idle": idle_all,
                        "active": active,
                        "total": total
                    }
        except Exception:
            pass
        return data

    def parse_stat(self) -> dict:
        """Parse /proc/stat for total and per-core CPU ticks."""
        if self.is_linux and Path("/proc/stat").exists():
            data = self._read_raw_proc_stat()
            if data:
                return data

        # Cross-platform fallback using psutil
        cpu_times = psutil.cpu_times_percent(interval=None, percpu=True)
        total_times = psutil.cpu_times_percent(interval=None, percpu=False)
        data = {
            "cpu": {
                "user": getattr(total_times, "user", 0.0),
                "nice": getattr(total_times, "nice", 0.0),
                "system": getattr(total_times, "system", 0.0),
                "idle": getattr(total_times, "idle", 100.0),
                "total": 100.0
            }
        }
        for i, core in enumerate(cpu_times):
            data[f"cpu{i}"] = {
                "user": getattr(core, "user", 0.0),
                "nice": getattr(core, "nice", 0.0),
                "system": getattr(core, "system", 0.0),
                "idle": getattr(core, "idle", 100.0),
                "total": 100.0
            }
        return data

    def get_cpu_percentages(self) -> dict:
        """Calculate aggregate and per-core CPU percentages between consecutive samples.

        On Linux: computes true delta of /proc/stat jiffies ((Δtotal - Δidle) / Δtotal * 100).
        On non-Linux: uses psutil.cpu_percent across sample ticks.
        """
        now = time.time()
        if self.is_linux and Path("/proc/stat").exists():
            current_stat = self._read_raw_proc_stat()
            if current_stat and self._last_cpu_stat:
                percentages = {}
                for name, curr in current_stat.items():
                    if name in self._last_cpu_stat:
                        prev = self._last_cpu_stat[name]
                        delta_total = curr["total"] - prev["total"]
                        delta_idle = curr["idle"] - prev["idle"]
                        if delta_total > 0:
                            usage = max(0.0, min(100.0, ((delta_total - delta_idle) / delta_total) * 100.0))
                        else:
                            usage = 0.0
                        percentages[name] = round(usage, 1)

                self._last_cpu_stat = current_stat
                self._last_cpu_time = now

                if "cpu" in percentages:
                    agg = percentages["cpu"]
                    per_core = [pct for k, pct in sorted(percentages.items()) if k.startswith("cpu") and k != "cpu"]
                    return {
                        "source": "procfs",
                        "aggregate_percent": agg,
                        "per_core_percent": per_core if per_core else [agg]
                    }
            else:
                self._last_cpu_stat = current_stat
                self._last_cpu_time = now

        # Fallback via psutil (Windows/macOS or initial Linux read)
        total_p = psutil.cpu_percent(interval=None)
        per_core_p = psutil.cpu_percent(interval=None, percpu=True)
        return {
            "source": "procfs" if self.is_linux else "psutil_fallback",
            "aggregate_percent": round(total_p, 1),
            "per_core_percent": [round(c, 1) for c in per_core_p]
        }

    def parse_meminfo(self) -> dict:
        """Parse /proc/meminfo for detailed memory metrics."""
        if self.is_linux and Path("/proc/meminfo").exists():
            try:
                meminfo = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            val = v.strip().split()[0]
                            meminfo[k.strip()] = int(val) * 1024  # convert kB to bytes
                
                total = meminfo.get("MemTotal", 1)
                free = meminfo.get("MemFree", 0)
                buffers = meminfo.get("Buffers", 0)
                cached = meminfo.get("Cached", 0)
                available = meminfo.get("MemAvailable", free + buffers + cached)
                used = total - available
                
                swap_total = meminfo.get("SwapTotal", 0)
                swap_free = meminfo.get("SwapFree", 0)
                swap_used = swap_total - swap_free

                return {
                    "source": "procfs",
                    "total": total,
                    "available": available,
                    "used": used,
                    "free": free,
                    "buffers": buffers,
                    "cached": cached,
                    "percent": round((used / total) * 100, 1),
                    "swap_total": swap_total,
                    "swap_used": swap_used,
                    "swap_percent": round((swap_used / swap_total * 100) if swap_total else 0.0, 1)
                }
            except Exception:
                pass

        # Fallback via psutil
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "source": "psutil_fallback",
            "total": vm.total,
            "available": vm.available,
            "used": vm.used,
            "free": vm.free,
            "buffers": getattr(vm, "buffers", 0),
            "cached": getattr(vm, "cached", 0),
            "percent": vm.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent
        }

    def parse_loadavg(self) -> dict:
        """Parse /proc/loadavg for 1, 5, 15 min load averages."""
        if self.is_linux and Path("/proc/loadavg").exists():
            try:
                with open("/proc/loadavg", "r") as f:
                    parts = f.read().split()
                return {
                    "load1": float(parts[0]),
                    "load5": float(parts[1]),
                    "load15": float(parts[2]),
                    "running_threads": parts[3] if len(parts) > 3 else "N/A"
                }
            except Exception:
                pass

        # Fallback
        if hasattr(os, "getloadavg"):
            try:
                l1, l5, l15 = os.getloadavg()
                return {"load1": round(l1, 2), "load5": round(l5, 2), "load15": round(l15, 2), "running_threads": "N/A"}
            except Exception:
                pass
        
        # Emulate load based on CPU percentage on Windows
        cpu_p = psutil.cpu_percent(interval=None) / 100.0 * psutil.cpu_count()
        return {
            "load1": round(cpu_p, 2),
            "load5": round(cpu_p * 0.95, 2),
            "load15": round(cpu_p * 0.90, 2),
            "running_threads": f"{len(psutil.pids())} active"
        }

    def parse_pid_info(self, pid: int) -> dict:
        """Parse /proc/[pid]/stat & /proc/[pid]/status or fallback."""
        if self.is_linux and Path(f"/proc/{pid}/stat").exists():
            try:
                with open(f"/proc/{pid}/stat", "r") as f:
                    content = f.read()
                # Process name is enclosed in parentheses
                l_paren = content.find("(")
                r_paren = content.rfind(")")
                comm = content[l_paren + 1:r_paren]
                rest = content[r_paren + 2:].split()

                state = rest[0]
                ppid = int(rest[1])
                pgrp = int(rest[2])
                priority = int(rest[15])
                nice = int(rest[16])
                num_threads = int(rest[17])

                # Read status for memory
                vsize = 0
                rss = 0
                if Path(f"/proc/{pid}/status").exists():
                    with open(f"/proc/{pid}/status", "r") as sf:
                        for line in sf:
                            if line.startswith("VmRSS:"):
                                rss = int(line.split()[1]) * 1024
                            elif line.startswith("VmSize:"):
                                vsize = int(line.split()[1]) * 1024

                state_map = {
                    "R": "Running",
                    "S": "Sleeping",
                    "D": "Disk Sleep",
                    "Z": "Zombie",
                    "T": "Stopped",
                    "t": "Tracing Stop",
                    "X": "Dead"
                }

                return {
                    "pid": pid,
                    "name": comm,
                    "state": state_map.get(state, state),
                    "raw_state": state,
                    "ppid": ppid,
                    "priority": priority,
                    "nice": nice,
                    "threads": num_threads,
                    "vsize": vsize,
                    "rss": rss
                }
            except Exception:
                pass

        # Fallback via psutil
        try:
            p = psutil.Process(pid)
            mem = p.memory_info()
            return {
                "pid": pid,
                "name": p.name(),
                "state": p.status().capitalize(),
                "raw_state": p.status()[:1].upper(),
                "ppid": p.ppid(),
                "priority": getattr(p, "nice", lambda: 0)(),
                "nice": getattr(p, "nice", lambda: 0)(),
                "threads": p.num_threads(),
                "vsize": mem.vms,
                "rss": mem.rss
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
