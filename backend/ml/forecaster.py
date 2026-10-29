"""Machine Learning Resource Usage Forecaster.

Fits polynomial and linear trend models over recent telemetry observations
to project CPU and Memory utilization into future time horizons (+10s, +30s, +60s).
Computes trend slopes, R² confidence metrics, and potential threshold breaches.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from .dataset_buffer import TelemetryBuffer
from ..config import CPU_HIGH_THRESHOLD, MEM_HIGH_THRESHOLD

class ResourceForecaster:
    """Predicts future system resource utilization using regression models."""

    def __init__(self, buffer: TelemetryBuffer):
        self.buffer = buffer

    def forecast(self, horizons: List[int] = None) -> Dict[str, Any]:
        """Generate forecasts for future horizons (seconds ahead)."""
        if horizons is None:
            horizons = [10, 30, 60]

        times, cpu_series, mem_series = self.buffer.get_feature_arrays()
        n_samples = len(times)

        # Normalize timestamps relative to the latest point
        t_latest = times[-1]
        x = (times - t_latest).reshape(-1, 1) # Values in [-history_len, 0]

        # Fit models for CPU
        model_cpu = make_pipeline(PolynomialFeatures(degree=1), Ridge(alpha=1.0))
        model_cpu.fit(x, cpu_series)
        r2_cpu = max(0.0, float(model_cpu.score(x, cpu_series)))

        # Fit models for Memory
        model_mem = make_pipeline(PolynomialFeatures(degree=1), Ridge(alpha=1.0))
        model_mem.fit(x, mem_series)
        r2_mem = max(0.0, float(model_mem.score(x, mem_series)))

        current_cpu = float(cpu_series[-1])
        current_mem = float(mem_series[-1])

        predictions = []
        alerts = []

        for h in horizons:
            x_future = np.array([[h]])
            pred_cpu = float(np.clip(model_cpu.predict(x_future)[0], 0.0, 100.0))
            pred_mem = float(np.clip(model_mem.predict(x_future)[0], 0.0, 100.0))

            pred_cpu = round(pred_cpu, 1)
            pred_mem = round(pred_mem, 1)

            predictions.append({
                "horizon_seconds": h,
                "predicted_cpu_percent": pred_cpu,
                "predicted_mem_percent": pred_mem,
                "cpu_delta": round(pred_cpu - current_cpu, 1),
                "mem_delta": round(pred_mem - current_mem, 1)
            })

            # Check threshold breaches
            if pred_cpu >= CPU_HIGH_THRESHOLD:
                alerts.append(f"Predicted CPU spike >= {CPU_HIGH_THRESHOLD}% within +{h}s ({pred_cpu}%)")
            if pred_mem >= MEM_HIGH_THRESHOLD:
                alerts.append(f"Predicted Memory exhaustion >= {MEM_HIGH_THRESHOLD}% within +{h}s ({pred_mem}%)")

        # Trend summary
        cpu_slope = round((predictions[-1]["predicted_cpu_percent"] - current_cpu) / horizons[-1], 3)
        mem_slope = round((predictions[-1]["predicted_mem_percent"] - current_mem) / horizons[-1], 3)

        return {
            "current_cpu": round(current_cpu, 1),
            "current_mem": round(current_mem, 1),
            "cpu_trend": "Increasing" if cpu_slope > 0.05 else ("Decreasing" if cpu_slope < -0.05 else "Stable"),
            "mem_trend": "Increasing" if mem_slope > 0.05 else ("Decreasing" if mem_slope < -0.05 else "Stable"),
            "cpu_slope_per_sec": cpu_slope,
            "mem_slope_per_sec": mem_slope,
            "confidence_r2": {
                "cpu": round(r2_cpu, 3),
                "mem": round(r2_mem, 3)
            },
            "predictions": predictions,
            "alerts": list(set(alerts)),
            "model_type": "Ridge Polynomial Regression (Online Time-Series)"
        }
