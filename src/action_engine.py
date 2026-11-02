import json
import secrets
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path.home()
STATE = HOME / ".local-agent"
REGISTRY = STATE / "project-registry.json"
PLANS = STATE / "plans"
AUDIT = STATE / "audit.jsonl"

PROTECTED_MODELS = {
    "embeddinggemma",
    "embeddinggemma:latest",
    "qwen36-agent-v2",
    "qwen36-agent-v2:latest",
}

STATE.mkdir(parents=True, exist_ok=True)
PLANS.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def command(args, timeout=60):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }


def load_registry():
    if not REGISTRY.exists():
        return {"projects": {}, "runtime_locks": {}, "policy": {}}
    return json.loads(REGISTRY.read_text())


def save_plan(plan):
    (PLANS / f"{plan['id']}.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    )


def load_plan(plan_id):
    path = PLANS / f"{plan_id}.json"
    if not path.exists():
        raise ValueError("תוכנית הפעולה לא נמצאה")
    return json.loads(path.read_text()), path


def audit(event):
    with AUDIT.open("a") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def docker_details(name):
    result = command(["docker", "inspect", name])
    if result["returncode"] != 0:
        raise ValueError(f"הקונטיינר לא נמצא: {name}")

    data = json.loads(result["stdout"])[0]
    state = data.get("State", {})
    labels = data.get("Config", {}).get("Labels") or {}

    return {
        "name": data["Name"].lstrip("/"),
        "running": bool(state.get("Running")),
        "status": state.get("Status"),
        "health": (state.get("Health") or {}).get("Status"),
        "project": labels.get("com.docker.compose.project"),
        "image": data.get("Config", {}).get("Image")
    }


def ollama_names():
    result = command(["ollama", "list"])
    if result["returncode"] != 0:
        raise ValueError(result["stderr"] or "לא ניתן לקרוא את Ollama")
    return {
        line.split()[0]
        for line in result["stdout"].splitlines()[1:]
        if line.strip()
    }


def protected_project_for_path(path, registry):
    for name, project in registry.get("projects", {}).items():
        configured = project.get("path")
        if not configured or not project.get("protected"):
            continue

        root = Path(configured).expanduser().resolve()
        if path == root or root in path.parents:
            return name
    return None


def plan(args):
    action = args.get("action")
    target = str(args.get("target", "")).strip()

    if action not in {"docker_stop", "ollama_remove", "trash_path"}:
        return {
            "error": "פעולה לא נתמכת",
            "allowed": ["docker_stop", "ollama_remove", "trash_path"]
        }

    if not target:
        return {"error": "חסר target"}

    registry = load_registry()
    strong = False
    details = {}

    if action == "docker_stop":
        details = docker_details(target)
        locked = target in registry.get("runtime_locks", {})
        project = details.get("project")
        project_protected = bool(
            registry.get("projects", {})
            .get(project or "", {})
            .get("protected")
        )

        strong = details["running"] or locked or project_protected

        if not details["running"]:
            return {
                "error": "הקונטיינר כבר אינו פעיל",
                "details": details
            }

    elif action == "ollama_remove":
        names = ollama_names()
        if target not in names:
            return {
                "error": "המודל אינו מופיע ב-ollama list",
                "target": target
            }

        strong = target in PROTECTED_MODELS
        details = {
            "installed": True,
            "protected_model": strong
        }

    elif action == "trash_path":
        path = Path(target).expanduser().resolve()

        if path == HOME or HOME not in path.parents:
            return {
                "error": "מותר להעביר לסל המחזור רק פריט בתוך תיקיית הבית"
            }

        if not path.exists():
            return {"error": "הנתיב אינו קיים", "path": str(path)}

        project = protected_project_for_path(path, registry)
        strong = project is not None

        details = {
            "path": str(path),
            "type": "directory" if path.is_dir() else "file",
            "protected_project": project
        }
        target = str(path)

    plan_id = secrets.token_hex(4)
    approval = (
        f"אשר בכוח {plan_id}"
        if strong
        else f"אשר {plan_id}"
    )

    record = {
        "id": plan_id,
        "created_at": now(),
        "status": "pending",
        "action": action,
        "target": target,
        "strong_approval": strong,
        "required_text": approval,
        "details": details
    }

    save_plan(record)

    return {
        "planned": True,
        "plan_id": plan_id,
        "action": action,
        "target": target,
        "details": details,
        "approval_required": approval,
        "message": "לא בוצע עדיין שום שינוי"
    }



def manage(args):
    operation = args.get("operation", "list")
    requested_id = str(args.get("plan_id", "")).strip()
    records = []

    for plan_path in sorted(
        PLANS.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True
    ):
        try:
            record = json.loads(plan_path.read_text())
        except Exception:
            continue

        if record.get("status") == "pending":
            created = datetime.fromisoformat(record["created_at"])
            if datetime.now(timezone.utc) - created > timedelta(minutes=30):
                record["status"] = "expired"
                record["expired_at"] = now()
                plan_path.write_text(
                    json.dumps(record, ensure_ascii=False, indent=2) + "\n"
                )

        records.append(record)

    if operation == "list":
        return {
            "plans": [
                {
                    "id": record.get("id"),
                    "status": record.get("status"),
                    "action": record.get("action"),
                    "target": record.get("target"),
                    "created_at": record.get("created_at")
                }
                for record in records[:20]
            ]
        }

    if operation == "cancel":
        if not requested_id:
            return {"error": "חסר plan_id"}

        record, plan_path = load_plan(requested_id)

        if record.get("status") != "pending":
            return {
                "error": "אפשר לבטל רק תוכנית ממתינה",
                "status": record.get("status")
            }

        record["status"] = "cancelled"
        record["cancelled_at"] = now()
        plan_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        )

        audit({
            "time": now(),
            "event": "plan_cancelled",
            "plan_id": requested_id,
            "action": record.get("action"),
            "target": record.get("target")
        })

        return {
            "cancelled": True,
            "plan_id": requested_id,
            "message": "התוכנית בוטלה ולא ניתן לבצע אותה"
        }

    return {"error": "operation חייב להיות list או cancel"}


def execute(args, user_text):
    plan_id = str(args.get("plan_id", "")).strip()
    plan_record, plan_path = load_plan(plan_id)

    if plan_record.get("status") != "pending":
        return {
            "error": "התוכנית כבר בוצעה או בוטלה",
            "status": plan_record.get("status")
        }

    created = datetime.fromisoformat(plan_record["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(minutes=30):
        plan_record["status"] = "expired"
        plan_record["expired_at"] = now()
        plan_path.write_text(
            json.dumps(plan_record, ensure_ascii=False, indent=2) + "\n"
        )
        return {
            "error": "תוכנית הפעולה פגה לאחר 30 דקות",
            "executed": False
        }

    expected = plan_record["required_text"]
    if user_text.strip() != expected:
        return {
            "error": "האישור אינו תואם",
            "required_text": expected,
            "executed": False
        }

    action = plan_record["action"]
    target = plan_record["target"]
    before = None
    undo = None

    if action == "docker_stop":
        before = docker_details(target)
        if not before["running"]:
            raise ValueError("הקונטיינר כבר נעצר; לא בוצעה פעולה")

        result = command(["docker", "stop", target], timeout=120)
        if result["returncode"] != 0:
            raise RuntimeError(result["stderr"])

        after = docker_details(target)
        success = not after["running"]
        undo = f"docker start {target}"

    elif action == "ollama_remove":
        if target not in ollama_names():
            raise ValueError("המודל כבר אינו מותקן")

        result = command(["ollama", "rm", target], timeout=300)
        if result["returncode"] != 0:
            raise RuntimeError(result["stderr"])

        after = {"installed": target in ollama_names()}
        success = not after["installed"]

    elif action == "trash_path":
        source = Path(target)
        if not source.exists():
            raise ValueError("הפריט כבר אינו קיים")

        trash = HOME / ".Trash"
        trash.mkdir(exist_ok=True)
        destination = trash / source.name

        if destination.exists():
            destination = trash / (
                f"{source.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                f"{source.suffix}"
            )

        before = {"path": str(source), "exists": True}
        shutil.move(str(source), str(destination))
        after = {
            "source_exists": source.exists(),
            "trash_path": str(destination),
            "trash_exists": destination.exists()
        }
        success = destination.exists() and not source.exists()
        undo = f"mv {json.dumps(str(destination))} {json.dumps(str(source))}"

    plan_record["status"] = "completed" if success else "failed"
    plan_record["executed_at"] = now()
    plan_record["before"] = before
    plan_record["after"] = after
    plan_record["undo"] = undo
    plan_path.write_text(
        json.dumps(plan_record, ensure_ascii=False, indent=2) + "\n"
    )

    audit({
        "time": now(),
        "plan_id": plan_id,
        "action": action,
        "target": target,
        "success": success,
        "before": before,
        "after": after,
        "undo": undo
    })

    return {
        "executed": success,
        "plan_id": plan_id,
        "action": action,
        "target": target,
        "verification": after,
        "undo": undo,
        "audit_log": str(AUDIT)
    }
