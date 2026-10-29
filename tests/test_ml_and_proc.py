"""Unit tests for ML Forecaster, Anomaly Detector, and /proc Parser."""

import pytest
from backend.core.proc_parser import ProcParser
from backend.core.system_metrics import SystemMetricsService
from backend.core.process_manager import ProcessManager
from backend.ml.dataset_buffer import TelemetryBuffer
from backend.ml.forecaster import ResourceForecaster
from backend.ml.anomaly_detector import AnomalyDetector

def test_proc_parser():
    parser = ProcParser()
    mem = parser.parse_meminfo()
    assert "total" in mem
    assert "used" in mem
    assert mem["total"] > 0

    load = parser.parse_loadavg()
    assert "load1" in load

    stat = parser.parse_stat()
    assert "cpu" in stat

def test_system_metrics_service():
    svc = SystemMetricsService()
    snap = svc.get_snapshot()
    assert "cpu" in snap
    assert "memory" in snap
    assert "disk" in snap
    assert "network" in snap
    assert "timestamp" in snap

def test_process_manager():
    pm = ProcessManager()
    procs = pm.get_process_list(limit=5)
    assert len(procs) > 0
    assert "pid" in procs[0]
    assert "name" in procs[0]

    tree = pm.get_process_tree()
    assert "roots" in tree

def test_ml_forecaster():
    buf = TelemetryBuffer(maxlen=30)
    # Populate mock data
    for i in range(15):
        buf.append({
            "timestamp": 1000 + i,
            "cpu": {"aggregate_percent": 30.0 + (i * 0.5)},
            "memory": {"percent": 50.0 + (i * 0.2), "used": 500000000, "swap_percent": 0.0},
            "disk": {"read_kb_s": 10, "write_kb_s": 20},
            "network": {"rx_kb_s": 5, "tx_kb_s": 5},
            "system": {"total_processes": 100}
        })

    forecaster = ResourceForecaster(buf)
    fc = forecaster.forecast(horizons=[10, 30])
    assert "predictions" in fc
    assert len(fc["predictions"]) == 2
    assert "cpu_trend" in fc

def test_anomaly_detector():
    detector = AnomalyDetector()
    res = detector.update_and_detect()
    assert "memory_leaks" in res
    assert "cpu_hogs" in res
    assert "status" in res
