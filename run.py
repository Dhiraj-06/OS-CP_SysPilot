"""SysPilot: Main Server Launcher.

Usage:
    python run.py
    python run.py --port 8001
"""

import sys
import socket
import argparse
import uvicorn
from backend.config import HOST as DEFAULT_HOST, PORT as DEFAULT_PORT

def is_port_in_use(host: str, port: int) -> bool:
    """Check if a specific host:port is already bound by another process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def find_available_port(host: str, start_port: int) -> int:
    """Find the next available port if start_port is occupied."""
    port = start_port
    while port < start_port + 20:
        if not is_port_in_use(host, port):
            return port
        port += 1
    return start_port

def main():
    parser = argparse.ArgumentParser(description="SysPilot Platform Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Bind port (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    host = args.host
    port = args.port

    if is_port_in_use(host, port):
        print("!" * 65)
        print(f"  WARNING: Port {port} is already in use by another process.")
        next_port = find_available_port(host, port + 1)
        print(f"  Switching to available port: {next_port}")
        print(f"  (Tip: If you want to use {port}, close the previous instance)")
        print("!" * 65)
        port = next_port

    print("=" * 65)
    print("  SysPilot: Intelligent Linux Process & Scheduling Platform")
    print("=" * 65)
    print(f"  Web Dashboard:       http://{host}:{port}")
    print(f"  API Docs (Swagger):  http://{host}:{port}/docs")
    print(f"  WebSocket Telemetry: ws://{host}:{port}/ws/telemetry")
    print("=" * 65)
    print("  Press Ctrl+C to stop the server.\n")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
