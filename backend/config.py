"""Configuration settings for SysPilot."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
FILE_SERVICE_STORAGE = DATA_DIR / "file_storage"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
FILE_SERVICE_STORAGE.mkdir(parents=True, exist_ok=True)

# Server Configuration
HOST = os.getenv("SYSPILOT_HOST", "127.0.0.1")
PORT = int(os.getenv("SYSPILOT_PORT", "8000"))
FILE_SERVICE_PORT = int(os.getenv("SYSPILOT_FILE_PORT", "8088"))

# Telemetry Configuration
TELEMETRY_INTERVAL_SECONDS = 1.0
HISTORICAL_BUFFER_SIZE = 120  # Keep 2 minutes of 1-second ticks

# ML & Anomaly Thresholds
CPU_HIGH_THRESHOLD = 85.0     # Percentage
MEM_HIGH_THRESHOLD = 85.0     # Percentage
LEAK_SLOPE_THRESHOLD = 0.5    # MB per second increase
FORECAST_HORIZONS = [10, 30, 60] # Seconds ahead
