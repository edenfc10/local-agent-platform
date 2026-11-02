import json
import secrets
import shlex
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

import file_intelligence

HOME = Path.home()
STATE = HOME / ".local-agent"
PLANS = STATE / "plans"
AUDIT = STATE / "audit.jsonl"

STATE.mkdir(parents=True, exist_ok=True)
PLANS.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(record):
    path = PLANS / f"{record['id']}.json"
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    )
    return path


def audit(event):
    with AUDIT.open("a") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def plan(args):
    requested = args.get("paths") or []

    if not isinstance(requested, list) or not requested:
        return {"error": "חובה לספק רשימת paths"}

    if len(requested) > 50:
        return {"error": "מותר לתכנן עד 50 קבצים בפעולה אחת"}

    protected = file_intelligence.protected_paths()
    items = []
    seen = set()

    for raw in requested:
        path = Path(str(raw)).expanduser().resolve()

        if str(path) in seen:
            continue
        seen.add(str(path))

        if path == HOME or HOME not in path.parents:
            return {
                "error": "מותר לפעול רק על קבצים בתוך תיקיית הבית",
                "path": str(path)
            }

        if not path.exists():
            return {"error": "הקובץ לא נמצא", "path": str(path)}

        if not path.is_file() or path.is_symlink():
            return {
                "error": "הפעולה הקבוצתית הנוכחית תומכת בקבצים רגילים בלבד",
                "path": str(path)
            }

        reason = file_intelligence.protection_reason(
            path, protected
        )
        if reason:
            return {
                "error": "הקובץ נמצא בנתיב מוגן",
                "path": str(path),
                "reason": reason
            }

        stat = path.stat()
        items.append({
            "path": str(path),
            "size": stat.st_size,
            "modified_ns": stat.st_mtime_ns
        })

    plan_id = secrets.token_hex(4)
    total = sum(item["size"] for item in items)

    record = {
        "id": plan_id,
        "created_at": now(),
        "status": "pending",
        "action": "trash_batch",
        "target": f"{len(items)} files",
        "items": items,
        "total_bytes": total,
        "required_text": f"אשר {plan_id}"
    }

    save(record)

    return {
        "planned": True,
        "plan_id": plan_id,
        "files": len(items),
        "total_bytes": total,
        "total_mb": round(total / 1024 / 1024, 1),
        "paths": [item["path"] for item in items],
        "approval_required": record["required_text"],
        "message": "לא הועבר או נמחק דבר"
    }


def execute(args, user_text):
    plan_id = str(args.get("plan_id", "")).strip()
    plan_path = PLANS / f"{plan_id}.json"

    if not plan_path.exists():
        return {"error": "תוכנית הפעולה לא נמצאה"}

    record = json.loads(plan_path.read_text())

    if record.get("action") != "trash_batch":
        return {"error": "זו אינה תוכנית קבוצתית"}

    if record.get("status") != "pending":
        return {
            "error": "התוכנית אינה ממתינה לביצוע",
            "status": record.get("status")
        }

    created = datetime.fromisoformat(record["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(minutes=30):
        record["status"] = "expired"
        record["expired_at"] = now()
        save(record)
        return {
            "error": "התוכנית פגה לאחר 30 דקות",
            "executed": False
        }

    if user_text.strip() != record["required_text"]:
        return {
            "error": "טקסט האישור אינו תואם",
            "required_text": record["required_text"],
            "executed": False
        }

    protected = file_intelligence.protected_paths()

    for item in record["items"]:
        source = Path(item["path"])

        if not source.exists():
            return {
                "error": "קובץ חסר; לא בוצעה שום העברה",
                "path": str(source)
            }

        stat = source.stat()
        if (
            stat.st_size != item["size"]
            or stat.st_mtime_ns != item["modified_ns"]
        ):
            return {
                "error": "קובץ השתנה מאז יצירת התוכנית",
                "path": str(source)
            }

        reason = file_intelligence.protection_reason(
            source, protected
        )
        if reason:
            return {
                "error": "הנתיב הפך למוגן; לא בוצעה פעולה",
                "path": str(source),
                "reason": reason
            }

    trash = HOME / ".Trash"
    trash.mkdir(exist_ok=True)
    moved = []

    try:
        for number, item in enumerate(record["items"], 1):
            source = Path(item["path"])
            destination = trash / source.name

            if destination.exists():
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                destination = trash / (
                    f"{source.stem}-{stamp}-{number}{source.suffix}"
                )

            shutil.move(str(source), str(destination))
            moved.append({
                "source": str(source),
                "trash": str(destination)
            })

    except Exception as error:
        rollback_errors = []

        for item in reversed(moved):
            try:
                shutil.move(item["trash"], item["source"])
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))

        return {
            "error": str(error),
            "rolled_back": not rollback_errors,
            "rollback_errors": rollback_errors
        }

    undo = [
        f"mv {shlex.quote(item['trash'])} {shlex.quote(item['source'])}"
        for item in moved
    ]

    record["status"] = "completed"
    record["executed_at"] = now()
    record["moved"] = moved
    record["undo"] = undo
    save(record)

    audit({
        "time": now(),
        "plan_id": plan_id,
        "action": "trash_batch",
        "success": True,
        "moved": moved,
        "undo": undo
    })

    return {
        "executed": True,
        "plan_id": plan_id,
        "files_moved": len(moved),
        "moved": moved,
        "undo": undo,
        "audit_log": str(AUDIT)
    }
