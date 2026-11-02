import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
DATA = HOME / ".local-agent"
STATE_FILE = DATA / "guardian-state.json"
EVENTS_FILE = DATA / "guardian-events.jsonl"
REGISTRY_FILE = DATA / "project-registry.json"
BACKGROUND_FILE = DATA / "background-status.json"

DATA.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now().astimezone().isoformat()


def run(command, timeout=30):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as error:
        return 1, "", str(error)


def load_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {} if default is None else default


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def cpu_busy():
    code, output, _ = run(["top", "-l", "1", "-n", "0"])
    if code:
        return None

    match = re.search(r"([\d.]+)%\s+idle", output)
    return round(100 - float(match.group(1)), 1) if match else None


def memory_free_percent():
    code, output, _ = run(["memory_pressure", "-Q"])
    if code:
        return None

    match = re.search(
        r"System-wide memory free percentage:\s*(\d+)%",
        output
    )
    return int(match.group(1)) if match else None


def swap_used_mb():
    code, output, _ = run(["sysctl", "-n", "vm.swapusage"])
    if code:
        return None

    match = re.search(r"used\s*=\s*([\d.]+)M", output)
    return round(float(match.group(1)), 1) if match else None


def disk_free_gb():
    return round(shutil.disk_usage(HOME).free / 1024**3, 1)


def docker_status():
    code, output, error = run([
        "docker", "ps", "--format",
        "{{.Names}}|{{.Status}}"
    ])

    if code:
        return {
            "available": False,
            "error": error.strip(),
            "containers": {}
        }

    containers = {}
    for line in output.splitlines():
        if "|" not in line:
            continue

        name, status = line.split("|", 1)
        containers[name] = status

    return {
        "available": True,
        "running": len(containers),
        "containers": containers
    }



def security_posture(current_ports):
    firewall_binary = (
        "/usr/libexec/ApplicationFirewall/"
        "socketfilterfw"
    )

    _, firewall_output, firewall_error = run(
        [firewall_binary, "--getglobalstate"]
    )

    firewall_text = (
        firewall_output or firewall_error
    ).strip()

    firewall_enabled = (
        "State = 1" in firewall_text
        or "enabled" in firewall_text.lower()
        and "disabled" not in firewall_text.lower()
    )

    public = []
    public_database_ports = []
    public_development_ports = []

    database_ports = {
        5432, 5433, 55432, 6379
    }

    development_ports = {
        3000, 3100,
        54321, 54322, 54323, 54324, 54327
    }

    approved_system = {
        ("ControlCe", 5000),
        ("ControlCe", 7000),
        ("rapportd", 56121),
        ("limactl", 53)
    }

    for listener in current_ports:
        if "|" not in listener:
            continue

        process, endpoint = listener.split("|", 1)

        if not (
            endpoint.startswith("*:")
            or endpoint.startswith("0.0.0.0:")
            or endpoint.startswith("[::]:")
        ):
            continue

        match = re.search(r":(\d+)$", endpoint)
        if not match:
            continue

        port = int(match.group(1))

        if (process, port) in approved_system:
            continue

        item = {
            "process": process,
            "endpoint": endpoint,
            "port": port
        }
        public.append(item)

        if port in database_ports:
            public_database_ports.append(item)

        if port in development_ports:
            public_development_ports.append(item)

    return {
        "firewall_enabled": firewall_enabled,
        "firewall_status": firewall_text,
        "public_listeners": public,
        "public_database_ports": public_database_ports,
        "public_development_ports": public_development_ports
    }

def protected_containers():
    registry = load_json(REGISTRY_FILE, {})
    locks = registry.get("runtime_locks", {})

    return sorted(
        name
        for name, details in locks.items()
        if details.get("protected", False)
    )


def ollama_processes():
    code, output, _ = run(["ollama", "ps"])
    if code:
        return {"available": False, "models": [], "heavy": []}

    lines = [
        line.strip()
        for line in output.splitlines()[1:]
        if line.strip()
    ]

    heavy = []
    for line in lines:
        size = re.search(r"([\d.]+)\s*GB", line)
        if size and float(size.group(1)) >= 12:
            heavy.append(line)

    return {
        "available": True,
        "models": lines,
        "heavy": heavy
    }


def listening_ports():
    code, output, _ = run([
        "/usr/sbin/lsof",
        "-nP",
        "-iTCP",
        "-sTCP:LISTEN"
    ])

    if code:
        return []

    listeners = set()

    for line in output.splitlines()[1:]:
        columns = line.split()
        if len(columns) < 9:
            continue

        process = columns[0].replace("\\x20", " ")
        endpoint = (
            columns[-2]
            if columns[-1] == "(LISTEN)"
            else columns[-1]
        )
        listeners.add(f"{process}|{endpoint}")

    return sorted(listeners)


def launch_agents():
    result = {}

    folder = HOME / "Library" / "LaunchAgents"
    if not folder.exists():
        return result

    for path in folder.glob("*.plist"):
        if path.name == "com.localagent.guardian.plist":
            continue

        try:
            result[path.name] = file_hash(path)
        except OSError:
            pass

    return result


def notify(title, message):
    script = (
        f"display notification {json.dumps(message)} "
        f"with title {json.dumps(title)}"
    )
    run(["osascript", "-e", script], timeout=10)


def record_event(event):
    with EVENTS_FILE.open("a") as file:
        file.write(
            json.dumps(event, ensure_ascii=False) + "\n"
        )


previous = load_json(STATE_FILE, {})
first_run = not bool(previous)

cpu = cpu_busy()
memory = memory_free_percent()
swap = swap_used_mb()
disk = disk_free_gb()
docker = docker_status()
protected = protected_containers()
ollama = ollama_processes()
ports = listening_ports()
agents = launch_agents()
background = load_json(BACKGROUND_FILE, {})
security = security_posture(ports)

previous_high_cpu = previous.get("high_cpu_count", 0)
high_cpu_count = (
    previous_high_cpu + 1
    if cpu is not None and cpu >= 85
    else 0
)

issues = []

if high_cpu_count >= 2:
    issues.append({
        "key": "cpu_high",
        "level": "warning",
        "message": f"CPU בעומס של {cpu}% בשתי בדיקות רצופות"
    })

if memory is not None and memory < 20:
    issues.append({
        "key": "memory_pressure",
        "level": "critical",
        "message": f"זיכרון פנוי לפי Memory Pressure: {memory}%"
    })

previous_swap = previous.get("swap_used_mb")
if (
    swap is not None
    and previous_swap is not None
    and swap - previous_swap >= 512
):
    issues.append({
        "key": "swap_growth",
        "level": "warning",
        "message": (
            f"ה־Swap גדל ב־{round(swap - previous_swap)}MB "
            f"והגיע ל־{swap}MB"
        )
    })

if disk < 100:
    issues.append({
        "key": "disk_low",
        "level": "critical",
        "message": f"נשארו רק {disk}GB פנויים בדיסק"
    })

if docker.get("available"):
    running = docker["containers"]

    for name in protected:
        if name not in running:
            issues.append({
                "key": f"protected_missing:{name}",
                "level": "critical",
                "message": f"קונטיינר מוגן אינו פעיל: {name}"
            })

    for name, status in running.items():
        if "(unhealthy)" in status.lower():
            issues.append({
                "key": f"docker_unhealthy:{name}",
                "level": "critical",
                "message": f"קונטיינר אינו בריא: {name}"
            })

for model in ollama.get("heavy", []):
    model_name = model.split()[0]
    issues.append({
        "key": f"heavy_model:{model_name}",
        "level": "warning",
        "message": f"מודל Ollama כבד נשאר טעון: {model_name}"
    })

if not first_run:
    for listener in sorted(set(ports) - set(previous.get("ports", []))):
        issues.append({
            "key": f"new_port:{listener}",
            "level": "security",
            "message": f"נפתח פורט חדש: {listener}"
        })

    old_agents = previous.get("launch_agents", {})

    for name, digest in agents.items():
        if name not in old_agents:
            issues.append({
                "key": f"new_agent:{name}",
                "level": "security",
                "message": f"נוסף LaunchAgent חדש: {name}"
            })
        elif old_agents[name] != digest:
            issues.append({
                "key": f"changed_agent:{name}",
                "level": "security",
                "message": f"LaunchAgent השתנה: {name}"
            })


if not security["firewall_enabled"]:
    issues.append({
        "key": "firewall_disabled",
        "level": "critical",
        "message": "חומת האש של macOS כבויה"
    })

if security["public_database_ports"]:
    exposed = ", ".join(
        str(item["port"])
        for item in security["public_database_ports"]
    )
    issues.append({
        "key": "public_database_ports",
        "level": "critical",
        "message": (
            "מסדי נתונים פתוחים לרשת בפורטים: "
            + exposed
        )
    })

if security["public_development_ports"]:
    exposed = ", ".join(
        str(item["port"])
        for item in security["public_development_ports"]
    )
    issues.append({
        "key": "public_development_ports",
        "level": "warning",
        "message": (
            "שירותי פיתוח פתוחים לרשת בפורטים: "
            + exposed
        )
    })

background_result = background.get("result")
if background_result not in (None, "success", "skipped_low_battery"):
    issues.append({
        "key": "background_failure",
        "level": "warning",
        "message": f"ריצת התחזוקה נכשלה: {background_result}"
    })

previous_active = set(previous.get("active_issue_keys", []))
current_active = {issue["key"] for issue in issues}

new_issues = [
    issue for issue in issues
    if issue["key"] not in previous_active
]

if not first_run:
    for issue in new_issues:
        event = {
            "time": now(),
            **issue
        }
        record_event(event)
        notify("Local Agent Guardian", issue["message"])

state = {
    "checked_at": now(),
    "first_run": first_run,
    "cpu_busy_percent": cpu,
    "high_cpu_count": high_cpu_count,
    "memory_free_percent": memory,
    "swap_used_mb": swap,
    "disk_free_gb": disk,
    "docker": docker,
    "protected_containers": protected,
    "ollama": ollama,
    "ports": ports,
    "launch_agents": agents,
    "background_result": background_result,
    "security": security,
    "active_issue_keys": sorted(current_active),
    "issues": issues
}

STATE_FILE.write_text(
    json.dumps(state, ensure_ascii=False, indent=2) + "\n"
)

summary = {
    "baseline_created": first_run,
    "cpu_busy_percent": cpu,
    "memory_free_percent": memory,
    "swap_used_mb": swap,
    "disk_free_gb": disk,
    "docker_running": docker.get("running"),
    "ollama_models_loaded": len(ollama.get("models", [])),
    "protected_containers": len(protected),
    "issues": issues
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
