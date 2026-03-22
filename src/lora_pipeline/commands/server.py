import os
import signal
import subprocess
import sys
from pathlib import Path

PID_FILE = Path("/tmp/lora_pipeline_http_server.pid")


def start(dest: Path) -> None:
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)
            print(f"Server already running (PID {pid})")
            return
        except ProcessLookupError:
            print("Stale PID file, cleaning up...")
            PID_FILE.unlink()

    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8000"],
        cwd=str(dest),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PID_FILE.write_text(str(proc.pid))
    print(f"Server started (PID {proc.pid}) serving {dest}")
    print("URL: http://localhost:8000")


def stop() -> None:
    if not PID_FILE.exists():
        print("No PID file found — is the server running?")
        return
    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"Server stopped (PID {pid})")
    except ProcessLookupError:
        print(f"Process {pid} not found (already stopped?)")
        PID_FILE.unlink()
