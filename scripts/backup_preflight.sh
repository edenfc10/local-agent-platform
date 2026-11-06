#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage:
  bash scripts/backup_preflight.sh [DESTINATION]

Performs read-only checks for a proposed backup destination and known local
sources. It never creates directories, copies data, reads secrets, starts
services or changes Docker/Colima state.

If DESTINATION is omitted, destination checks are reported as NOT TESTED.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

destination="${1:-}"
failures=0
warnings=0

section() {
  printf '\n===== %s =====\n' "$1"
}

pass() {
  printf 'PASS: %s\n' "$1"
}

warn() {
  printf 'WARN: %s\n' "$1"
  warnings=$((warnings + 1))
}

fail() {
  printf 'FAIL: %s\n' "$1"
  failures=$((failures + 1))
}

section "AUDIT METADATA"
date '+Checked: %Y-%m-%d %H:%M:%S %z'
printf 'Mode: read-only backup preflight\n'
printf 'Host: %s\n' "$(scutil --get ComputerName 2>/dev/null || hostname)"

section "REQUIRED COMMANDS"
for command_name in shasum df stat find git docker; do
  if command -v "$command_name" >/dev/null 2>&1; then
    pass "$command_name is available"
  else
    warn "$command_name is unavailable"
  fi
done

section "DESTINATION"
if [[ -z "$destination" ]]; then
  warn "No destination supplied; off-device readiness is NOT TESTED"
elif [[ ! -e "$destination" ]]; then
  fail "Destination does not exist: $destination"
else
  canonical_destination="$(cd "$destination" 2>/dev/null && pwd -P)"
  if [[ -z "${canonical_destination:-}" ]]; then
    fail "Destination is not accessible: $destination"
  else
    printf 'Path: %s\n' "$canonical_destination"
    if [[ -d "$canonical_destination" ]]; then
      pass "Destination is a directory"
    else
      fail "Destination is not a directory"
    fi

    if [[ -r "$canonical_destination" ]]; then
      pass "Destination is readable"
    else
      fail "Destination is not readable"
    fi

    if [[ -w "$canonical_destination" ]]; then
      pass "Destination is writable by the current user"
    else
      warn "Destination is not writable by the current user"
    fi

    destination_device="$(df "$canonical_destination" 2>/dev/null | awk 'NR==2 {print $1}')"
    root_device="$(df "$HOME" 2>/dev/null | awk 'NR==2 {print $1}')"
    printf 'Destination device: %s\n' "${destination_device:-unknown}"
    printf 'Home device: %s\n' "${root_device:-unknown}"

    if [[ -n "${destination_device:-}" && "$destination_device" != "$root_device" ]]; then
      pass "Destination is on a different mounted filesystem"
    else
      warn "Destination appears to share the home filesystem; this is not off-device protection"
    fi

    df -h "$canonical_destination" 2>/dev/null || true

    if command -v diskutil >/dev/null 2>&1; then
      volume_info="$(diskutil info "$canonical_destination" 2>/dev/null || true)"
      if printf '%s\n' "$volume_info" | grep -Eq 'FileVault:.*Yes|Encrypted:.*Yes'; then
        pass "Destination reports encryption"
      else
        warn "Destination encryption was not verified"
      fi
    else
      warn "diskutil is unavailable; encryption is NOT TESTED"
    fi
  fi
fi

section "KNOWN SOURCE PATHS"
check_path() {
  label="$1"
  source_path="$2"

  if [[ -e "$source_path" ]]; then
    pass "$label exists: $source_path"
  else
    warn "$label not found: $source_path"
  fi
}

check_path "AIJAA verified dump"   "$HOME/Backups/AIJAA/20261104-234034/aijaa-default-postgres.dump"
check_path "AIJAA checksum manifest"   "$HOME/Backups/AIJAA/20261104-234034/SHA256SUMS"
check_path "Local-agent runtime" "$HOME/.local-agent"
check_path "Local-agent source" "$HOME/local-agent"
check_path "Ollama data" "$HOME/.ollama"
check_path "Colima data" "$HOME/.colima"

section "AIJAA CHECKSUM"
aijaa_manifest="$HOME/Backups/AIJAA/20261104-234034/SHA256SUMS"
if [[ -f "$aijaa_manifest" ]]; then
  manifest_dir="$(dirname "$aijaa_manifest")"
  if (cd "$manifest_dir" && shasum -a 256 -c "$(basename "$aijaa_manifest")"); then
    pass "AIJAA local backup checksum matches"
  else
    fail "AIJAA local backup checksum failed"
  fi
else
  warn "AIJAA checksum manifest is unavailable"
fi

section "PROTECTED DOCKER STATE"
if command -v colima >/dev/null 2>&1; then
  colima list 2>/dev/null || warn "Could not read Colima profile list"
else
  warn "Colima CLI is unavailable"
fi

default_socket="$HOME/.colima/default/docker.sock"
if [[ -S "$default_socket" ]]; then
  pass "Default Docker socket exists"
  docker --host "unix://$default_socket" ps     --format 'container={{.Names}} status={{.Status}}' 2>/dev/null     || warn "Could not read containers from the default profile"
  docker --host "unix://$default_socket" volume ls     --format 'volume={{.Name}}' 2>/dev/null     || warn "Could not read volumes from the default profile"
else
  warn "Default Docker socket not found; profile was not started"
fi

section "RESULT"
printf 'Failures: %d\n' "$failures"
printf 'Warnings: %d\n' "$warnings"
printf 'No files, services, containers, volumes or Git state were changed.\n'
printf 'No environment values, credentials or database records were read.\n'

if (( failures > 0 )); then
  exit 1
fi
