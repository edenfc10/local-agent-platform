import json
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / ".local-agent/network-remediation-plan.json"

TARGETS = [
    "fitforyou-db",
    "fitforyou-db-test",
    "open-webui",
    "supabase_db_rebbestay",
    "supabase_studio_rebbestay",
    "supabase_inbucket_rebbestay",
    "supabase_kong_rebbestay",
    "supabase_analytics_rebbestay"
]


def run(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as error:
        return 1, "", str(error)


def inspect_container(name):
    code, output, error = run([
        "docker", "inspect", name
    ])

    if code:
        return {
            "name": name,
            "error": error
        }

    data = json.loads(output)[0]
    labels = data.get("Config", {}).get("Labels") or {}
    host = data.get("HostConfig", {})

    return {
        "name": name,
        "state": data.get("State", {}).get("Status"),
        "health": (
            data.get("State", {})
            .get("Health", {})
            .get("Status")
        ),
        "image": data.get("Config", {}).get("Image"),
        "port_bindings": host.get("PortBindings") or {},
        "restart_policy": (
            host.get("RestartPolicy", {}).get("Name")
        ),
        "compose_project": labels.get(
            "com.docker.compose.project"
        ),
        "compose_working_dir": labels.get(
            "com.docker.compose.project.working_dir"
        ),
        "compose_config_files": labels.get(
            "com.docker.compose.project.config_files"
        ),
        "supabase_project": labels.get(
            "com.supabase.cli.project"
        )
    }


def node_3100():
    code, output, _ = run([
        "/usr/sbin/lsof",
        "-nP",
        "-iTCP:3100",
        "-sTCP:LISTEN",
        "-Fpctn"
    ])

    if code or not output:
        return {"found": False}

    pid = None

    for line in output.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = line[1:]
            break

    if not pid:
        return {
            "found": True,
            "raw": output
        }

    _, process, _ = run([
        "ps", "-p", pid,
        "-o", "pid=,%cpu=,%mem=,rss=,etime=,command="
    ])

    _, cwd_output, _ = run([
        "/usr/sbin/lsof",
        "-a",
        "-p", pid,
        "-d", "cwd",
        "-Fn"
    ])

    cwd = None
    for line in cwd_output.splitlines():
        if line.startswith("n"):
            cwd = line[1:]
            break

    return {
        "found": True,
        "pid": int(pid),
        "cwd": cwd,
        "process": process
    }


containers = [
    inspect_container(name)
    for name in TARGETS
]

plan = {
    "created_at": datetime.now().astimezone().isoformat(),
    "status": "review_only",
    "executed": False,
    "firewall": {
        "proposed": "enable_macos_application_firewall",
        "requires_admin_password": True,
        "executed": False
    },
    "containers": containers,
    "node_3100": node_3100(),
    "proposed_policy": {
        "databases": "bind to 127.0.0.1 only",
        "supabase": "bind to 127.0.0.1 unless LAN access is required",
        "open_webui": (
            "bind locally; remote access later through Tailscale"
        ),
        "node_3100": "identify before deciding",
        "volumes": "never remove",
        "containers": "restart only after exact approval"
    }
}

OUTPUT.write_text(
    json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
)

print("===== CONTAINER SOURCES =====")

for container in containers:
    print(f"\n{container['name']}")
    if container.get("error"):
        print("  error:", container["error"])
        continue

    print("  state:", container["state"])
    print("  health:", container["health"])
    print("  image:", container["image"])
    print("  compose project:", container["compose_project"])
    print("  working dir:", container["compose_working_dir"])
    print("  config files:", container["compose_config_files"])
    print("  port bindings:")
    print(json.dumps(
        container["port_bindings"],
        ensure_ascii=False,
        indent=4
    ))

print("\n===== NODE PORT 3100 =====")
print(json.dumps(
    plan["node_3100"],
    ensure_ascii=False,
    indent=2
))

print(f"\nהתוכנית נשמרה: {OUTPUT}")
print("לא בוצעו שינויים.")
