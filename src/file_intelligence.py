import hashlib
import json
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
REGISTRY = HOME / ".local-agent" / "project-registry.json"

DEFAULT_ROOTS = [
    HOME / "Desktop",
    HOME / "Downloads",
    HOME / "Documents",
    HOME / "Code",
]

SKIP_DIRS = {
    ".git", ".svn", "node_modules", ".venv", "venv",
    "__pycache__", ".next", "dist", "build", "coverage",
    "site-packages", "uv-cache", "archive-v0",
}

ARCHIVES = {
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz",
    ".7z", ".rar",
}

INSTALLERS = {
    ".dmg", ".pkg", ".iso",
}

PROJECT_MARKERS = {
    ".git", "package.json", "pyproject.toml", "go.mod",
    "Cargo.toml", "pom.xml", "docker-compose.yml",
    "docker-compose.yaml", "compose.yml", "compose.yaml",
}


def format_size(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024


def load_registry():
    if not REGISTRY.exists():
        return {"projects": {}}
    try:
        return json.loads(REGISTRY.read_text())
    except Exception:
        return {"projects": {}}


def docker_bind_paths():
    try:
        ids = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True,
            text=True,
            timeout=20
        ).stdout.split()

        if not ids:
            return set()

        result = subprocess.run(
            ["docker", "inspect", *ids],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return set()

        protected = set()
        for container in json.loads(result.stdout):
            for mount in container.get("Mounts", []):
                if mount.get("Type") == "bind" and mount.get("Source"):
                    protected.add(
                        str(Path(mount["Source"]).expanduser().resolve())
                    )
        return protected
    except Exception:
        return set()


def protected_paths():
    paths = docker_bind_paths()
    registry = load_registry()

    for project in registry.get("projects", {}).values():
        if project.get("protected") and project.get("path"):
            paths.add(
                str(Path(project["path"]).expanduser().resolve())
            )

    return sorted(paths)


def protection_reason(path, protected):
    resolved = str(path.resolve())

    for root in protected:
        if resolved == root or resolved.startswith(root.rstrip("/") + "/"):
            return f"protected path: {root}"

    return None


def digest_file(path):
    sha = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            block = file.read(4 * 1024 * 1024)
            if not block:
                break
            sha.update(block)

    return sha.hexdigest()


def scan(args):
    roots = [
        Path(item).expanduser().resolve()
        for item in args.get("roots", [])
    ] or DEFAULT_ROOTS

    minimum_mb = max(1, int(args.get("minimum_mb", 100)))
    duplicate_minimum_mb = max(
        1, int(args.get("duplicate_minimum_mb", 10))
    )
    old_days = max(1, int(args.get("old_days", 30)))
    limit = min(max(10, int(args.get("limit", 80))), 300)

    minimum_bytes = minimum_mb * 1024 * 1024
    duplicate_minimum_bytes = duplicate_minimum_mb * 1024 * 1024
    old_before = time.time() - old_days * 86400
    protected = protected_paths()

    files = []
    projects = []
    errors = []
    root_totals = defaultdict(int)
    same_size = defaultdict(list)

    for root in roots:
        if not root.exists():
            errors.append(f"missing root: {root}")
            continue

        for base, dirs, names in os.walk(root, followlinks=False):
            base_path = Path(base)

            dirs[:] = [
                name for name in dirs
                if name not in SKIP_DIRS
                and not (base_path / name).is_symlink()
            ]

            present = set(dirs) | set(names)
            markers = sorted(PROJECT_MARKERS.intersection(present))

            if markers:
                reason = protection_reason(base_path, protected)
                projects.append({
                    "path": str(base_path),
                    "markers": markers,
                    "protected": bool(reason),
                    "protection_reason": reason,
                })

            for name in names:
                path = base_path / name

                try:
                    if path.is_symlink() or not path.is_file():
                        continue

                    stat = path.stat()
                    logical = stat.st_size
                    allocated = (
                        stat.st_blocks * 512
                        if hasattr(stat, "st_blocks")
                        else logical
                    )

                    root_totals[str(root)] += allocated

                    if logical >= duplicate_minimum_bytes:
                        same_size[logical].append(path)

                    suffix = path.suffix.lower()
                    old = stat.st_mtime < old_before
                    reasons = []

                    if logical >= minimum_bytes:
                        reasons.append("large file")

                    if old and suffix in INSTALLERS:
                        reasons.append("old installer")

                    if old and suffix in ARCHIVES:
                        reasons.append("old archive")

                    if not reasons:
                        continue

                    protected_reason = protection_reason(path, protected)

                    files.append({
                        "path": str(path),
                        "logical_bytes": logical,
                        "logical_size": format_size(logical),
                        "allocated_bytes": allocated,
                        "allocated_size": format_size(allocated),
                        "age_days": int(
                            (time.time() - stat.st_mtime) / 86400
                        ),
                        "reasons": reasons,
                        "protected": bool(protected_reason),
                        "protection_reason": protected_reason,
                    })

                except (PermissionError, OSError) as error:
                    if len(errors) < 30:
                        errors.append(f"{path}: {error}")

    duplicate_groups = []

    for size, paths in same_size.items():
        if len(paths) < 2:
            continue

        hashes = defaultdict(list)

        for path in paths:
            try:
                hashes[digest_file(path)].append(path)
            except (PermissionError, OSError) as error:
                if len(errors) < 30:
                    errors.append(f"{path}: {error}")

        for digest, matches in hashes.items():
            if len(matches) < 2:
                continue

            duplicate_groups.append({
                "sha256": digest,
                "size_each": format_size(size),
                "potential_saving": format_size(
                    size * (len(matches) - 1)
                ),
                "paths": [str(path) for path in matches],
                "protected": any(
                    protection_reason(path, protected)
                    for path in matches
                ),
            })

    files.sort(
        key=lambda item: item["allocated_bytes"],
        reverse=True
    )

    duplicate_groups.sort(
        key=lambda item: len(item["paths"]),
        reverse=True
    )

    return {
        "read_only": True,
        "settings": {
            "roots": [str(root) for root in roots],
            "minimum_mb": minimum_mb,
            "duplicate_minimum_mb": duplicate_minimum_mb,
            "old_days": old_days,
        },
        "root_allocated_sizes": {
            root: format_size(size)
            for root, size in root_totals.items()
        },
        "protected_paths": protected,
        "projects": projects[:limit],
        "candidates": files[:limit],
        "duplicate_groups": duplicate_groups[:30],
        "errors": errors,
        "summary": {
            "projects_found": len(projects),
            "candidates_found": len(files),
            "duplicate_groups_found": len(duplicate_groups),
        },
    }
