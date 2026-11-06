#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage:
  bash scripts/verify_backup_manifest.sh MANIFEST.sha256

Validates files listed in a SHA-256 manifest. The manifest must use the format
produced by "shasum -a 256". Relative paths are resolved from the manifest's
directory.

This script does not restore, copy, modify or delete backup data.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

manifest="${1:-}"
if [[ -z "$manifest" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -f "$manifest" ]]; then
  printf 'ERROR: manifest does not exist: %s\n' "$manifest" >&2
  exit 2
fi

if [[ ! -r "$manifest" ]]; then
  printf 'ERROR: manifest is not readable: %s\n' "$manifest" >&2
  exit 2
fi

if ! command -v shasum >/dev/null 2>&1; then
  printf 'ERROR: shasum is unavailable\n' >&2
  exit 2
fi

manifest_dir="$(cd "$(dirname "$manifest")" && pwd -P)"
manifest_name="$(basename "$manifest")"

printf '===== BACKUP MANIFEST VERIFICATION =====\n'
printf 'Manifest: %s/%s\n' "$manifest_dir" "$manifest_name"
date '+Checked: %Y-%m-%d %H:%M:%S %z'

if [[ ! -s "$manifest" ]]; then
  printf 'ERROR: manifest is empty\n' >&2
  exit 1
fi

entry_count="$(awk 'NF >= 2 && $1 ~ /^[0-9a-fA-F]{64}$/ {count++} END {print count+0}' "$manifest")"
printf 'Entries: %s\n' "$entry_count"

if [[ "$entry_count" -eq 0 ]]; then
  printf 'ERROR: manifest contains no valid SHA-256 entries\n' >&2
  exit 1
fi

if (cd "$manifest_dir" && shasum -a 256 -c "$manifest_name"); then
  printf 'PASS: all listed checksums match\n'
  printf 'No backup data was modified.\n'
  exit 0
fi

printf 'FAIL: one or more checksums did not match\n' >&2
printf 'No backup data was modified.\n' >&2
exit 1
