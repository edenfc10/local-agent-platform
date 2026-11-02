import fcntl
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
AGENT_DIR = HOME / "local-agent"
STATE_DIR = HOME / ".local-agent"
LOCK_FILE = STATE_DIR / "background.lock"
STATUS_FILE = STATE_DIR / "background-status.json"

STATE_DIR.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def battery_status():
    try:
        result = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True,
            text=True,
            timeout=10
        )
        text = result.stdout
        power = (
            "battery"
            if "Battery Power" in text
            else "ac"
        )

        percent = None
        for token in text.replace(";", " ").split():
            if token.endswith("%"):
                percent = int(token.rstrip("%"))
                break

        return {"power": power, "percent": percent}
    except Exception as error:
        return {"power": "unknown", "error": str(error)}


def docker_status():
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {
                "available": False,
                "error": result.stderr.strip()
            }

        containers = [
            line for line in result.stdout.splitlines()
            if line.strip()
        ]

        return {
            "available": True,
            "running": len(containers),
            "containers": containers
        }
    except Exception as error:
        return {"available": False, "error": str(error)}


def save_status(data):
    STATUS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )


def main():
    with LOCK_FILE.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return

        battery = battery_status()
        disk = shutil.disk_usage(HOME)

        status = {
            "started_at": now(),
            "battery": battery,
            "disk_free_gb": round(disk.free / 1024**3, 1),
            "docker": docker_status(),
            "index": None
        }

        if (
            battery.get("power") == "battery"
            and battery.get("percent") is not None
            and battery["percent"] < 35
        ):
            status["result"] = "skipped_low_battery"
            status["finished_at"] = now()
            save_status(status)
            return

        result = subprocess.run(
            [sys.executable, str(AGENT_DIR / "agent.py"), "index"],
            cwd=AGENT_DIR,
            capture_output=True,
            text=True,
            timeout=1200
        )

        status["index"] = {
            "returncode": result.returncode,
            "stdout": result.stdout.strip()[-4000:],
            "stderr": result.stderr.strip()[-4000:]
        }
        status["result"] = (
            "success" if result.returncode == 0 else "failed"
        )
        status["finished_at"] = now()
        save_status(status)


if __name__ == "__main__":
    main()
