"""SysPilot: Unified FastAPI Application & Real-time WebSocket Server.

Coordinates all 7 OS project objectives:
1. Real-time Process & Kernel Telemetry (/ws/telemetry & /api/system/*)
2. CPU Scheduling Simulator & Recommender (/api/scheduler/*)
3. Concurrency, Deadlock & IPC Lab (/api/concurrency/*)
4. Multi-Client Concurrent File Service (/api/file_service/*)
5. Machine Learning Resource Forecaster (/api/ml/*)
6. Static Web Dashboard Hosting (/)
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import FRONTEND_DIR, TELEMETRY_INTERVAL_SECONDS, HISTORICAL_BUFFER_SIZE
from .core import ProcessManager, SystemMetricsService, ProcParser
from .scheduler import SchedulingSimulator, SchedulingRecommender
from .scheduler.streaming_simulator import StreamingSimulator
from .concurrency import BankersAlgorithm, BoundedBufferSimulator, ReadersWritersSimulator, IPCService
from .file_service import ConcurrentFileServer, ClientHarness
from .ml import TelemetryBuffer, ResourceForecaster, AnomalyDetector

app = FastAPI(
    title="SysPilot Platform",
    description="Intelligent Linux Process, Resource Management and Scheduling Optimization Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize core singletons
proc_manager = ProcessManager()
metrics_service = SystemMetricsService()
proc_parser = ProcParser()

scheduler_sim = SchedulingSimulator()
scheduler_rec = SchedulingRecommender()
streaming_sim = StreamingSimulator()

bounded_buffer_sim = BoundedBufferSimulator(capacity=6)
readers_writers_sim = ReadersWritersSimulator()

file_server = ConcurrentFileServer()
file_harness = ClientHarness(file_server)

telemetry_buffer = TelemetryBuffer(maxlen=HISTORICAL_BUFFER_SIZE)
forecaster = ResourceForecaster(telemetry_buffer)
anomaly_detector = AnomalyDetector()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

ws_manager = ConnectionManager()

# Background telemetry broadcaster
async def telemetry_broadcast_loop():
    while True:
        try:
            snapshot = metrics_service.get_snapshot()
            telemetry_buffer.append(snapshot)

            # Predict future trend
            fc = forecaster.forecast()
            # Check anomalies
            anom = anomaly_detector.update_and_detect()
            # Top 10 processes
            top_procs = proc_manager.get_process_list(limit=12, sort_by="cpu_percent")

            payload = {
                "type": "telemetry_tick",
                "system": snapshot,
                "forecast": fc,
                "anomalies": anom,
                "top_processes": top_procs
            }

            await ws_manager.broadcast(payload)
        except Exception:
            pass
        await asyncio.sleep(TELEMETRY_INTERVAL_SECONDS)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(telemetry_broadcast_loop())

# WebSocket Routes
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Streaming Scheduler WebSocket
@app.websocket("/ws/scheduler/simulate")
async def websocket_scheduler_simulate(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive simulation request
        data = await websocket.receive_text()
        req = json.loads(data)

        algorithm = req.get("algorithm")
        processes = req.get("processes", [])
        params = req.get("params", {})
        speed = req.get("speed", 1.0)  # Simulation speed multiplier

        # Generate and stream events
        for event in streaming_sim.simulate(algorithm, processes, params):
            await websocket.send_json(event)
            # Control playback speed (base delay 100ms per time unit)
            await asyncio.sleep(0.1 / speed)

            # Check for control messages (pause/resume)
            try:
                control_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                control = json.loads(control_msg)
                if control.get("action") == "pause":
                    # Wait for resume
                    while True:
                        resume_msg = await websocket.receive_text()
                        resume = json.loads(resume_msg)
                        if resume.get("action") == "resume":
                            break
                        elif resume.get("action") == "stop":
                            return
                elif control.get("action") == "stop":
                    return
                elif control.get("action") == "speed":
                    speed = control.get("value", 1.0)
            except asyncio.TimeoutError:
                pass

        # Send completion event
        await websocket.send_json({
            "event": "SIMULATION_COMPLETE",
            "makespan": streaming_sim.makespan
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

# -------------------------------------------------------------
# 1. System & Process Management API Endpoints
# -------------------------------------------------------------
@app.get("/api/system/metrics")
def get_system_metrics():
    return metrics_service.get_snapshot()

@app.get("/api/system/proc_info")
def get_proc_raw_info():
    return {
        "meminfo": proc_parser.parse_meminfo(),
        "loadavg": proc_parser.parse_loadavg(),
        "stat_cores": proc_parser.parse_stat()
    }

@app.get("/api/processes")
def get_processes(limit: int = 50, sort_by: str = "cpu_percent"):
    return proc_manager.get_process_list(limit=limit, sort_by=sort_by)

@app.get("/api/processes/tree")
def get_process_tree():
    return proc_manager.get_process_tree()

@app.get("/api/processes/zombies")
def get_zombies():
    return proc_manager.get_zombies_and_orphans()

class SignalRequest(BaseModel):
    pid: int
    signal_name: str

@app.post("/api/processes/signal")
def send_signal(req: SignalRequest):
    res = proc_manager.send_signal(req.pid, req.signal_name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

class ReniceRequest(BaseModel):
    pid: int
    nice_value: int

@app.post("/api/processes/renice")
def renice_process(req: ReniceRequest):
    res = proc_manager.renice_process(req.pid, req.nice_value)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

# -------------------------------------------------------------
# 2. CPU Scheduling API Endpoints
# -------------------------------------------------------------
class ProcessItem(BaseModel):
    pid: int
    name: Optional[str] = None
    arrival_time: int
    burst_time: int
    priority: Optional[int] = 0

class SimulationRequest(BaseModel):
    algorithm: str
    processes: List[ProcessItem]
    params: Optional[Dict[str, Any]] = None

@app.post("/api/scheduler/simulate")
def simulate_schedule(req: SimulationRequest):
    procs = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in req.processes]
    try:
        return scheduler_sim.run_algorithm(req.algorithm, procs, req.params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CompareRequest(BaseModel):
    processes: List[ProcessItem]
    params: Optional[Dict[str, Any]] = None

@app.post("/api/scheduler/compare")
def compare_schedules(req: CompareRequest):
    procs = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in req.processes]
    return scheduler_sim.compare_all(procs, req.params)

@app.post("/api/scheduler/recommend")
def recommend_schedule(req: CompareRequest):
    procs = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in req.processes]
    return scheduler_rec.recommend(procs, req.params)

# -------------------------------------------------------------
# 3. Concurrency, Deadlock & IPC API Endpoints
# -------------------------------------------------------------
class BankersSafetyRequest(BaseModel):
    available: List[int]
    allocation: List[List[int]]
    max_matrix: List[List[int]]

@app.post("/api/concurrency/bankers/safety")
def bankers_safety(req: BankersSafetyRequest):
    try:
        return BankersAlgorithm.is_safe_state(req.available, req.allocation, req.max_matrix)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class BankersResourceRequest(BaseModel):
    pid: int
    request: List[int]
    available: List[int]
    allocation: List[List[int]]
    max_matrix: List[List[int]]

@app.post("/api/concurrency/bankers/request")
def bankers_request_resource(req: BankersResourceRequest):
    try:
        return BankersAlgorithm.request_resources(
            req.pid, req.request, req.available, req.allocation, req.max_matrix
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SyncSimRequest(BaseModel):
    producers: Optional[int] = 2
    consumers: Optional[int] = 2
    capacity: Optional[int] = 5
    ops: Optional[int] = 4

@app.post("/api/concurrency/producer_consumer")
def run_producer_consumer(req: SyncSimRequest):
    sim = BoundedBufferSimulator(capacity=req.capacity)
    return sim.run_simulation(req.producers, req.consumers, req.ops)

class RWSimRequest(BaseModel):
    readers: Optional[int] = 4
    writers: Optional[int] = 2
    iterations: Optional[int] = 3

@app.post("/api/concurrency/readers_writers")
def run_readers_writers(req: RWSimRequest):
    return readers_writers_sim.run_simulation(req.readers, req.writers, req.iterations)

@app.get("/api/concurrency/ipc_benchmark")
def run_ipc_benchmark():
    return IPCService.run_benchmark()

# -------------------------------------------------------------
# 4. Multi-Client Concurrent File Service API Endpoints
# -------------------------------------------------------------
@app.get("/api/file_service/status")
def get_file_service_status():
    return file_server.get_status()

@app.get("/api/file_service/files")
def list_files():
    return file_server.list_files()

class FileReadRequest(BaseModel):
    client_id: str
    filename: str

@app.post("/api/file_service/read")
def read_file(req: FileReadRequest):
    return file_server.read_file(req.client_id, req.filename)

class FileWriteRequest(BaseModel):
    client_id: str
    filename: str
    content: str

@app.post("/api/file_service/write")
def write_file(req: FileWriteRequest):
    return file_server.write_file(req.client_id, req.filename, req.content)

@app.post("/api/file_service/append")
def append_file(req: FileWriteRequest):
    return file_server.append_file(req.client_id, req.filename, req.content)

class StressTestRequest(BaseModel):
    num_clients: Optional[int] = 6
    operations_per_client: Optional[int] = 8

@app.post("/api/file_service/stress_test")
def run_file_stress_test(req: StressTestRequest):
    return file_harness.run_stress_test(req.num_clients, req.operations_per_client)

# -------------------------------------------------------------
# 5. Machine Learning & Anomaly Detection API Endpoints
# -------------------------------------------------------------
@app.get("/api/ml/forecast")
def get_resource_forecast():
    return forecaster.forecast()

@app.get("/api/ml/anomalies")
def get_anomalies():
    return anomaly_detector.update_and_detect()

class AnomalySimRequest(BaseModel):
    anomaly_type: str
    duration_seconds: Optional[int] = 15

@app.post("/api/ml/simulate_anomaly")
def simulate_anomaly(req: AnomalySimRequest):
    return anomaly_detector.simulate_anomaly(req.anomaly_type, req.duration_seconds)

# -------------------------------------------------------------
# 6. Static Files & Frontend Mount
# -------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
