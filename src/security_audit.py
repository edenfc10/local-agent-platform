import hashlib
import json
import plistlib
import re
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
DATA = HOME / ".local-agent"
REPORT = DATA / "security-audit.json"

DATA.mkdir(parents=True, exist_ok=True)


def run(command, timeout=30):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as error:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(error)
        }


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def port_number(endpoint):
    match = re.search(r":(\d+)$", endpoint)
    return int(match.group(1)) if match else None


def risk_for(port, process):
    if port in {5432, 5433, 55432, 6379}:
        return {
            "level": "high",
            "reason": "מסד נתונים או Redis; מומלץ שיהיה מקומי בלבד"
        }

    if port in {2375, 2376}:
        return {
            "level": "critical",
            "reason": "Docker API על הרשת"
        }

    if port in {54321, 54322, 54323, 54324, 54327}:
        return {
            "level": "medium",
            "reason": "שירות Supabase לפיתוח"
        }

    if port in {3000, 3100, 8080, 8790}:
        return {
            "level": "medium",
            "reason": "ממשק Web או שירות פיתוח"
        }

    if process in {"ControlCe", "rapportd"}:
        return {
            "level": "system",
            "reason": "שירות macOS מוכר"
        }

    return {
        "level": "review",
        "reason": "שירות רשת שדורש זיהוי"
    }


def listeners():
    result = run([
        "/usr/sbin/lsof",
        "-nP",
        "-iTCP",
        "-sTCP:LISTEN"
    ])

    items = []

    for line in result["stdout"].splitlines()[1:]:
        columns = line.split()

        if len(columns) < 9:
            continue

        process = columns[0].replace("\\x20", " ")
        pid = columns[1]
        user = columns[2]
        endpoint = (
            columns[-2]
            if columns[-1] == "(LISTEN)"
            else columns[-1]
        )

        port = port_number(endpoint)
        public = (
            endpoint.startswith("*:")
            or endpoint.startswith("0.0.0.0:")
            or endpoint.startswith("[::]:")
        )

        risk = risk_for(port, process)

        items.append({
            "process": process,
            "pid": int(pid) if pid.isdigit() else pid,
            "user": user,
            "endpoint": endpoint,
            "port": port,
            "public": public,
            "risk": risk["level"],
            "reason": risk["reason"]
        })

    return sorted(
        items,
        key=lambda item: (
            not item["public"],
            item["port"] or 0,
            item["process"]
        )
    )


def docker_ports():
    result = run([
        "docker",
        "ps",
        "--format",
        "{{.Names}}\t{{.Ports}}"
    ])

    containers = []

    for line in result["stdout"].splitlines():
        if "\t" in line:
            name, ports = line.split("\t", 1)
        else:
            name, ports = line, ""

        containers.append({
            "name": name.strip(),
            "ports": ports.strip()
        })

    return containers


def firewall():
    binary = (
        "/usr/libexec/ApplicationFirewall/"
        "socketfilterfw"
    )

    global_state = run([binary, "--getglobalstate"])
    stealth = run([binary, "--getstealthmode"])

    return {
        "global_state": global_state["stdout"] or global_state["stderr"],
        "stealth_mode": stealth["stdout"] or stealth["stderr"]
    }


def safe_arguments(arguments):
    safe = []

    for argument in arguments[:8]:
        value = str(argument).replace(str(HOME), "~")

        if re.search(
            r"token|secret|password|api[_-]?key",
            value,
            re.IGNORECASE
        ):
            value = "[REDACTED]"

        safe.append(value)

    return safe


def inspect_launch_agent(name):
    path = HOME / "Library" / "LaunchAgents" / name

    if not path.exists():
        return {
            "name": name,
            "exists": False
        }

    try:
        with path.open("rb") as file:
            data = plistlib.load(file)

        arguments = data.get("ProgramArguments", [])
        program = data.get("Program")

        return {
            "name": name,
            "exists": True,
            "path": str(path),
            "label": data.get("Label"),
            "program": (
                str(program).replace(str(HOME), "~")
                if program else None
            ),
            "program_arguments": safe_arguments(arguments),
            "environment_keys": sorted(
                data.get("EnvironmentVariables", {}).keys()
            ),
            "run_at_load": data.get("RunAtLoad", False),
            "keep_alive": data.get("KeepAlive", False),
            "sha256": sha256(path)
        }

    except Exception as error:
        return {
            "name": name,
            "exists": True,
            "error": str(error)
        }


all_listeners = listeners()
public_listeners = [
    item for item in all_listeners
    if item["public"]
]

launch_agents = [
    inspect_launch_agent("ai.openclaw.gateway.plist"),
    inspect_launch_agent("ai.hermes.gateway.plist"),
    inspect_launch_agent("com.localagent.maintenance.plist"),
    inspect_launch_agent("com.localagent.guardian.plist")
]

report = {
    "generated_at": datetime.now().astimezone().isoformat(),
    "read_only": True,
    "summary": {
        "listeners_total": len(all_listeners),
        "public_listeners": len(public_listeners),
        "high_or_critical": sum(
            item["risk"] in {"high", "critical"}
            for item in public_listeners
        ),
        "docker_containers": len(docker_ports())
    },
    "firewall": firewall(),
    "public_listeners": public_listeners,
    "docker": docker_ports(),
    "launch_agents": launch_agents
}

REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)

print("===== SECURITY SUMMARY =====")
print(json.dumps(
    report["summary"],
    ensure_ascii=False,
    indent=2
))

print("\n===== FIREWALL =====")
print(json.dumps(
    report["firewall"],
    ensure_ascii=False,
    indent=2
))

print("\n===== PUBLIC LISTENERS =====")
for item in public_listeners:
    print(
        f"[{item['risk'].upper()}] "
        f"{item['process']} pid={item['pid']} "
        f"{item['endpoint']} — {item['reason']}"
    )

print("\n===== DOCKER PORTS =====")
for container in report["docker"]:
    if container["ports"]:
        print(
            f"{container['name']}: "
            f"{container['ports']}"
        )

print("\n===== WATCHED LAUNCH AGENTS =====")
for agent in launch_agents:
    print(json.dumps(
        agent,
        ensure_ascii=False,
        indent=2
    ))

print(f"\nהדוח נשמר: {REPORT}")
