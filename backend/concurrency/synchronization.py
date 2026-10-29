"""Process Synchronization Primitives & Classical Problems.

Implements:
1. Producer-Consumer Problem (Bounded Buffer)
   - Synchronized using Semaphores: `empty`, `full`, and `mutex` Lock.
   - Prevents buffer overflow and underflow while avoiding race conditions.

2. Readers-Writers Problem
   - Reader-preference vs Writer-preference synchronization.
   - Demonstrates starvation prevention and mutual exclusion on shared data.
"""

import threading
import time
import random
from typing import List, Dict, Any

class BoundedBufferSimulator:
    """Producer-Consumer bounded buffer simulator using semaphores."""

    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.buffer = []
        self.mutex = threading.Lock()
        self.empty = threading.Semaphore(capacity)
        self.full = threading.Semaphore(0)
        self.logs = []
        self.is_running = False
        self.produced_count = 0
        self.consumed_count = 0

    def run_simulation(self, num_producers: int = 2, num_consumers: int = 2, operations_per_worker: int = 5) -> Dict[str, Any]:
        """Execute synchronized multi-threaded Producer-Consumer simulation."""
        self.buffer.clear()
        self.logs.clear()
        self.produced_count = 0
        self.consumed_count = 0
        self.empty = threading.Semaphore(self.capacity)
        self.full = threading.Semaphore(0)

        threads = []

        def producer_worker(p_id: int):
            for i in range(operations_per_worker):
                item = f"Item_{p_id}_{i+1}"
                # Wait for empty slot
                self.empty.acquire()
                with self.mutex:
                    self.buffer.append(item)
                    self.produced_count += 1
                    current_state = list(self.buffer)
                    self.logs.append({
                        "timestamp": time.time(),
                        "actor": f"Producer-{p_id}",
                        "action": f"Produced '{item}'",
                        "buffer_size": len(current_state),
                        "buffer_state": current_state
                    })
                # Signal full slot
                self.full.release()
                time.sleep(random.uniform(0.01, 0.05))

        def consumer_worker(c_id: int):
            for _ in range(operations_per_worker):
                # Wait for full slot
                self.full.acquire()
                with self.mutex:
                    if self.buffer:
                        item = self.buffer.pop(0)
                        self.consumed_count += 1
                        current_state = list(self.buffer)
                        self.logs.append({
                            "timestamp": time.time(),
                            "actor": f"Consumer-{c_id}",
                            "action": f"Consumed '{item}'",
                            "buffer_size": len(current_state),
                            "buffer_state": current_state
                        })
                # Signal empty slot
                self.empty.release()
                time.sleep(random.uniform(0.01, 0.05))

        # Launch threads
        for p in range(num_producers):
            t = threading.Thread(target=producer_worker, args=(p + 1,))
            threads.append(t)
            t.start()

        for c in range(num_consumers):
            t = threading.Thread(target=consumer_worker, args=(c + 1,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return {
            "capacity": self.capacity,
            "total_produced": self.produced_count,
            "total_consumed": self.consumed_count,
            "final_buffer": list(self.buffer),
            "events_count": len(self.logs),
            "events": self.logs[-40:]  # Last 40 events for UI display
        }


class ReadersWritersSimulator:
    """Readers-Writers problem with writer starvation avoidance."""

    def __init__(self):
        self.shared_data = "Initial OS Kernel State"
        self.read_count = 0
        self.read_count_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.service_queue = threading.Lock() # Prevents writer starvation (FIFO entry)
        self.logs = []

    def run_simulation(self, num_readers: int = 4, num_writers: int = 2, iterations: int = 3) -> Dict[str, Any]:
        """Run synchronized readers and writers simulation."""
        self.logs.clear()
        self.read_count = 0
        threads = []

        def reader_worker(r_id: int):
            for _ in range(iterations):
                # Request service entry
                with self.service_queue:
                    with self.read_count_lock:
                        self.read_count += 1
                        if self.read_count == 1:
                            self.write_lock.acquire() # First reader locks writer
                
                # Reading section (shared read)
                current_readers = self.read_count
                self.logs.append({
                    "timestamp": time.time(),
                    "actor": f"Reader-{r_id}",
                    "action": f"READING shared value: '{self.shared_data}'",
                    "active_readers": current_readers,
                    "active_writers": 0
                })
                time.sleep(random.uniform(0.01, 0.03))

                with self.read_count_lock:
                    self.read_count -= 1
                    if self.read_count == 0:
                        self.write_lock.release() # Last reader releases writer lock

                time.sleep(random.uniform(0.01, 0.04))

        def writer_worker(w_id: int):
            for it in range(iterations):
                # Writer requests service entry
                with self.service_queue:
                    self.write_lock.acquire()

                # Critical section: Exclusive write
                new_val = f"State_v{w_id}_{it+1}"
                self.shared_data = new_val
                self.logs.append({
                    "timestamp": time.time(),
                    "actor": f"Writer-{w_id}",
                    "action": f"EXCLUSIVE WRITE: updated shared value to '{new_val}'",
                    "active_readers": 0,
                    "active_writers": 1
                })
                time.sleep(random.uniform(0.02, 0.05))

                self.write_lock.release()
                time.sleep(random.uniform(0.02, 0.05))

        for w in range(num_writers):
            t = threading.Thread(target=writer_worker, args=(w + 1,))
            threads.append(t)
            t.start()

        for r in range(num_readers):
            t = threading.Thread(target=reader_worker, args=(r + 1,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return {
            "final_shared_value": self.shared_data,
            "total_events": len(self.logs),
            "events": self.logs[-40:]
        }
