"""Process Manager: Process hierarchy, tree construction, state tracking & signals.

Implements core OS process management capabilities:
- Process table generation with CPU%, Memory%, Priority, Nice, State
- Process Tree hierarchy (Parent-Child graph from PPID linkages)
- Zombie / Orphan process detection
- POSIX signal dispatch: SIGTERM (15), SIGKILL (9), SIGSTOP (19), SIGCONT (18)
- Priority / Nice value tuning (renice)
"""

from typing import List, Dict, Any, Optional
import os
import signal
import psutil
from .proc_parser import ProcParser

class ProcessManager:
    """Manages system processes, process hierarchies, and signal operations."""

    def __init__(self):
        self.proc_parser = ProcParser()

    def get_process_list(self, limit: int = 100, sort_by: str = "cpu_percent") -> List[Dict[str, Any]]:
        """Get enriched list of running processes."""
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'ppid', 'create_time', 'num_threads']):
            try:
                info = p.info
                # Basic memory info
                mem_rss = 0
                try:
                    mem_rss = p.memory_info().rss
                except Exception:
                    pass

                # Nice value
                nice_val = 0
                try:
                    nice_val = p.nice()
                except Exception:
                    pass

                processes.append({
                    "pid": info["pid"],
                    "ppid": info["ppid"] or 0,
                    "name": info["name"] or "Unknown",
                    "username": info["username"] or "system",
                    "status": (info["status"] or "unknown").capitalize(),
                    "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                    "memory_percent": round(info["memory_percent"] or 0.0, 1),
                    "rss_bytes": mem_rss,
                    "rss_formatted": self._format_bytes(mem_rss),
                    "num_threads": info["num_threads"] or 1,
                    "nice": nice_val,
                    "is_zombie": (info["status"] == psutil.STATUS_ZOMBIE) if hasattr(psutil, "STATUS_ZOMBIE") else False,
                    "is_orphan": info["ppid"] == 1 and info["pid"] != 1
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort
        reverse = True
        if sort_by in ["pid", "ppid", "name", "nice"]:
            reverse = False
        
        processes.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        return processes[:limit]

    def get_process_tree(self) -> Dict[str, Any]:
        """Construct the complete process hierarchy tree (parent-child graph)."""
        nodes = {}
        children_map = {}

        for p in psutil.process_iter(['pid', 'name', 'ppid', 'status', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                pid = info['pid']
                ppid = info['ppid'] or 0
                nodes[pid] = {
                    "pid": pid,
                    "ppid": ppid,
                    "name": info['name'] or f"proc_{pid}",
                    "status": (info['status'] or "unknown").capitalize(),
                    "cpu_percent": round(info['cpu_percent'] or 0.0, 1),
                    "memory_percent": round(info['memory_percent'] or 0.0, 1),
                    "children": []
                }
                if ppid not in children_map:
                    children_map[ppid] = []
                children_map[ppid].append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Attach children to parents
        root_nodes = []
        for pid, node in nodes.items():
            ppid = node["ppid"]
            if ppid in nodes and ppid != pid:
                nodes[ppid]["children"].append(node)
            else:
                # Top level node (init/systemd/system idle or detached)
                root_nodes.append(node)

        return {
            "total_nodes": len(nodes),
            "roots": root_nodes[:15]  # Limit top-level roots for visualization speed
        }

    def get_zombies_and_orphans(self) -> Dict[str, Any]:
        """Detect and analyze zombie and orphan processes."""
        zombies = []
        orphans = []

        for p in psutil.process_iter(['pid', 'name', 'ppid', 'status']):
            try:
                info = p.info
                status = info['status']
                if status == getattr(psutil, "STATUS_ZOMBIE", "zombie"):
                    zombies.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "ppid": info["ppid"],
                        "description": "Terminated process with entry remaining in process table awaiting parent wait() call."
                    })
                elif info["ppid"] == 1 and info["pid"] != 1:
                    orphans.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "ppid": 1,
                        "description": "Parent process terminated before child; adopted by init/systemd (PID 1)."
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "zombies_count": len(zombies),
            "orphans_count": len(orphans),
            "zombies": zombies,
            "orphans": orphans
        }

    def send_signal(self, pid: int, sig_name: str) -> Dict[str, Any]:
        """Send a POSIX or OS control signal to a target process."""
        sig_map = {
            "SIGTERM": getattr(signal, "SIGTERM", 15),
            "SIGKILL": getattr(signal, "SIGKILL", 9),
            "SIGSTOP": getattr(signal, "SIGSTOP", None),
            "SIGCONT": getattr(signal, "SIGCONT", None)
        }

        if sig_name not in sig_map:
            return {"success": False, "error": f"Unsupported signal: {sig_name}"}

        try:
            p = psutil.Process(pid)
            if sig_name == "SIGTERM":
                p.terminate()
            elif sig_name == "SIGKILL":
                p.kill()
            elif sig_name == "SIGSTOP":
                p.suspend()
            elif sig_name == "SIGCONT":
                p.resume()
            return {"success": True, "message": f"Signal {sig_name} dispatched to PID {pid}"}
        except psutil.NoSuchProcess:
            return {"success": False, "error": f"Process PID {pid} does not exist"}
        except psutil.AccessDenied:
            return {"success": False, "error": f"Permission denied to signal PID {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def renice_process(self, pid: int, nice_value: int) -> Dict[str, Any]:
        """Adjust process scheduling priority (nice value from -20 to 19)."""
        try:
            # Clamp between -20 and 19
            nice_val = max(-20, min(19, int(nice_value)))
            p = psutil.Process(pid)
            p.nice(nice_val)
            return {"success": True, "message": f"PID {pid} reniced to {nice_val}"}
        except psutil.NoSuchProcess:
            return {"success": False, "error": f"Process PID {pid} does not exist"}
        except psutil.AccessDenied:
            return {"success": False, "error": f"Permission denied to change priority of PID {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _format_bytes(self, num_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"
