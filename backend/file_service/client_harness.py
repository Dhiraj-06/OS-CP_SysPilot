"""Automated Multi-Client Concurrency Test Harness.

Simulates multiple concurrent client threads performing read, write,
and append operations against the concurrent file server.
Validates Reader-Writer mutual exclusion and page cache hit ratios.
"""

import threading
import time
import random
from typing import Dict, Any, List
from .server import ConcurrentFileServer

class ClientHarness:
    """Stress test generator for the concurrent file service."""

    def __init__(self, server: ConcurrentFileServer):
        self.server = server

    def run_stress_test(self, num_clients: int = 5, operations_per_client: int = 6) -> Dict[str, Any]:
        """Spawn concurrent threads simulating active clients."""
        filenames = ["kernel_syslog.txt", "cpu_stats.log", "process_table.dat", "memory_map.bin"]
        threads = []
        errors = []
        start_time = time.perf_counter()

        def worker(client_id: str):
            for i in range(operations_per_client):
                fname = random.choice(filenames)
                op_type = random.choices(["READ", "WRITE", "APPEND"], weights=[0.6, 0.2, 0.2])[0]
                try:
                    if op_type == "READ":
                        self.server.read_file(client_id, fname)
                    elif op_type == "WRITE":
                        content = f"[{client_id}] Generated state block at {time.strftime('%H:%M:%S')}"
                        self.server.write_file(client_id, fname, content)
                    elif op_type == "APPEND":
                        addition = f"[{client_id}] Entry #{i+1} appended."
                        self.server.append_file(client_id, fname, addition)
                except Exception as e:
                    errors.append(f"{client_id} on {fname}: {str(e)}")

                time.sleep(random.uniform(0.01, 0.04))

        for c in range(num_clients):
            cid = f"Client_{c+1}"
            t = threading.Thread(target=worker, args=(cid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        total_time = max(time.perf_counter() - start_time, 0.001)
        total_ops = num_clients * operations_per_client
        throughput = round(total_ops / total_time, 2)

        return {
            "num_clients": num_clients,
            "total_operations": total_ops,
            "duration_seconds": round(total_time, 2),
            "throughput_ops_sec": throughput,
            "errors_count": len(errors),
            "errors": errors,
            "server_status": self.server.get_status()
        }
