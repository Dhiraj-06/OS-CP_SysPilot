"""Quick end-to-end HTTP and API verification script."""

import urllib.request
import json

def post_json(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())

def main():
    print("Testing SysPilot Server Endpoints...")

    # 1. System Metrics
    metrics = get_json("http://127.0.0.1:8000/api/system/metrics")
    assert "cpu" in metrics and "memory" in metrics
    print("[PASS] System Metrics API")

    # 2. Process listing
    procs = get_json("http://127.0.0.1:8000/api/processes?limit=10")
    assert len(procs) > 0
    print(f"[PASS] Process List API ({len(procs)} processes returned)")

    # 3. CPU Scheduling Simulation (Round Robin)
    sched = post_json("http://127.0.0.1:8000/api/scheduler/simulate", {
        "algorithm": "round_robin",
        "processes": [
            {"pid": 1, "name": "P1", "arrival_time": 0, "burst_time": 5, "priority": 1},
            {"pid": 2, "name": "P2", "arrival_time": 1, "burst_time": 3, "priority": 2}
        ],
        "params": {"quantum": 2}
    })
    assert sched["makespan"] == 8
    print(f"[PASS] CPU Scheduler API (Makespan: {sched['makespan']}, Avg WT: {sched['metrics']['avg_waiting_time']})")

    # 4. Scheduling Recommender
    rec = post_json("http://127.0.0.1:8000/api/scheduler/recommend", {
        "processes": [
            {"pid": 1, "name": "P1", "arrival_time": 0, "burst_time": 2, "priority": 1},
            {"pid": 2, "name": "P2", "arrival_time": 0, "burst_time": 20, "priority": 2}
        ]
    })
    assert "recommended_algorithm" in rec
    print(f"[PASS] Scheduling Recommender API (Recommended: {rec['recommended_algorithm']['name']})")

    # 5. Banker's Algorithm (Safe State)
    bankers = post_json("http://127.0.0.1:8000/api/concurrency/bankers/safety", {
        "available": [3, 3, 2],
        "allocation": [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2]
        ],
        "max_matrix": [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3]
        ]
    })
    assert bankers["is_safe"] is True
    print(f"[PASS] Banker's Algorithm API (Safe Sequence: {bankers['safe_sequence_str']})")

    # 6. Multi-Client Concurrent File Service
    stress = post_json("http://127.0.0.1:8000/api/file_service/stress_test", {
        "num_clients": 4,
        "operations_per_client": 5
    })
    assert stress["total_operations"] == 20
    print(f"[PASS] Concurrent File Service Stress Test ({stress['total_operations']} ops @ {stress['throughput_ops_sec']} ops/sec)")

    # 7. Machine Learning Forecast
    fc = get_json("http://127.0.0.1:8000/api/ml/forecast")
    assert "predictions" in fc
    print(f"[PASS] ML Resource Forecaster API (Current CPU: {fc['current_cpu']}%, Horizon +10s: {fc['predictions'][0]['predicted_cpu_percent']}%)")

    # 8. Anomaly Detector
    anom = get_json("http://127.0.0.1:8000/api/ml/anomalies")
    assert "status" in anom
    print(f"[PASS] Anomaly Detector API (Status: {anom['status']})")

    print("\nALL 8 CORE SYSTEM API ENDPOINTS OPERATIONAL & VERIFIED!")

if __name__ == "__main__":
    main()
