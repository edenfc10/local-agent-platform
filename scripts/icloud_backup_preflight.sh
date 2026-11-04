#!/usr/bin/env bash
set -u

icloud_root="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
backup_dir="$HOME/Backups/AIJAA/20261104-234034"
manifest="$backup_dir/SHA256SUMS"

failures=0
warnings=0

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

printf '===== ICLOUD BACKUP PREFLIGHT =====\n'
date '+Checked: %Y-%m-%d %H:%M:%S %z'
printf 'Mode: read-only\n\n'

if [[ -d "$icloud_root" ]]; then
  pass "iCloud Drive directory exists"
else
  fail "iCloud Drive directory is unavailable"
fi

if [[ -r "$icloud_root" ]]; then
  pass "iCloud Drive directory is readable"
else
  fail "iCloud Drive directory is not readable"
fi

if [[ -w "$icloud_root" ]]; then
  pass "iCloud Drive directory is writable by the current user"
else
  fail "iCloud Drive directory is not writable by the current user"
fi

if command -v brctl >/dev/null 2>&1; then
  if brctl status >/dev/null 2>&1; then
    pass "macOS iCloud document service responds"
  else
    warn "iCloud document service status could not be confirmed"
  fi
else
  warn "brctl is unavailable"
fi

printf '\n===== SOURCE BACKUP =====\n'
if [[ -d "$backup_dir" ]]; then
  pass "AIJAA backup directory exists"
else
  fail "AIJAA backup directory is unavailable"
fi

if [[ -f "$manifest" ]]; then
  pass "AIJAA checksum manifest exists"
  if (cd "$backup_dir" && shasum -a 256 -c "$(basename "$manifest")"); then
    pass "AIJAA local backup checksum matches"
  else
    fail "AIJAA local backup checksum failed"
  fi
else
  fail "AIJAA checksum manifest is unavailable"
fi

printf '\n===== CAPACITY NOTES =====\n'
df -h "$HOME" 2>/dev/null || true
printf '%s\n' "Local free space is shown above."
printf '%s\n' "iCloud remote quota is NOT TESTED by this script."

printf '\n===== RESULT =====\n'
printf 'Failures: %d\n' "$failures"
printf 'Warnings: %d\n' "$warnings"
printf '%s\n' "No file was created, copied, uploaded, restored or deleted."
printf '%s\n' "No credentials, environment values or database records were read."
printf '%s\n' "A passing preflight does not prove that a file synchronized to iCloud."

if (( failures > 0 )); then
  exit 1
fi
