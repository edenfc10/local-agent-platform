# Current State

Updated: 2026-11-06

The canonical discovery, risk register and roadmap are in
`docs/HOME_LAB_MASTER_PLAN.md`.

## Implemented local-agent capabilities

- Local Ollama models
- `embeddinggemma` embeddings
- File indexing and lexical search
- Scoped semantic RAG
- Persistent SQLite memory
- Disk, project, Docker and Ollama inventory tools
- File scanning and duplicate detection
- Single and batch action planning
- Exact approval checks
- Audit and undo information
- Protected project/container registry
- Guardian resource and network monitoring
- Background incremental file indexing
- Tailscale access to selected local interfaces

## Runtime locations

- Runtime state: `~/.local-agent`
- Model data: `~/.ollama`
- Working installation: `~/local-agent`
- Versioned source: `src/` in this repository

Runtime databases, backups and model data are not copied into Git.

## Verified host baseline

- MacBook Pro M1 Max, arm64, 64 GB unified memory, 1 TB SSD
- macOS 15.7.7
- Current storage follow-up: 227 GiB used, 650 GiB free, 26% capacity
- Colima allocated storage: approximately 59 GB
  - `default`: approximately 28.6 GB
  - `aijaa-ci`: approximately 6.6 GB
  - `rebbestay-actions`: approximately 8.2 GB
  - `rebbestay-ci`: approximately 16.1 GB
- Ollama data approximately 56 GB
- CPU approximately 83% idle during the main snapshot
- Four running Colima profiles:
  - `default`: 8 CPU / 16 GiB / 120 GiB logical disk
  - `aijaa-ci`: 4 CPU / 8 GiB / 60 GiB
  - `rebbestay-actions`: 4 CPU / 10 GiB / 60 GiB
  - `rebbestay-ci`: 4 CPU / 10 GiB / 60 GiB
- No Ollama model was loaded during the original resource audit
- macOS firewall enabled
- Tailscale active
- No Time Machine destination or local snapshot was found

## Protected workloads

The Colima `default` profile is protected. It contains active development
services including RebbeStay, Open WebUI, FitForYou databases, Supabase and the
currently protected AIJAA database.

No unrelated change may stop or recreate this profile.

## AIJAA recovery status

- Active code worktree:
  `~/Code/AIJAA/aijaa-reconcile`
- Latest observed branch: `feat/wp1-submit-safety`
- Verified branch: `feat/wp1-submit-safety`
- Verified HEAD: `23efeb8c95c311f90b82b9782541c57e23f19ddd`
- Working tree clean; local and remote branch HEADs match
- PR #5 push and pull-request CI passed at this commit
- Canonical local runtime: Colima `default`
- Localhost forwarding: PostgreSQL `127.0.0.1:55432`, Redis
  `127.0.0.1:6379`
- Protected database revision: `6c1a9d4e2f70`
- Source migration head: `9a3c7e1f5b20`
- One migration is pending on the protected database
- Logical backup created under `~/Backups/AIJAA/20261104-234034`
- Backup SHA-256:
  `affa575bcbed823c38d381ddc28976ed9d66b8272f8c56e798b346eeace876a8`
- Isolated restore succeeded with 29 tables and approximately 23 rows
- No migration was applied to the protected database
- No off-device copy has been verified

## Backup and recovery foundation

- `docs/BACKUP_RECOVERY.md` defines protected workloads, backup tiers,
  provisional RPO/RTO targets, encryption, retention and restore proof.
- `scripts/backup_preflight.sh` performs read-only destination and source
  checks; it does not copy data or change services.
- `scripts/verify_backup_manifest.sh` validates SHA-256 manifests without
  restoring or modifying backup data.
- The AIJAA logical dump remains the only restore-verified workload.
- No external SSD is currently available (REPORTED).
- iCloud Drive and OneDrive Personal directories are present (VERIFIED).
- iCloud Drive is the selected interim encrypted-copy destination; quota,
  synchronization and cloud recovery remain NOT TESTED.
- No live backup, copy, restore or retention operation is authorized by this
  documentation change.

## GitHub Actions

### RebbeStay

- Runner: `eden-mac-rebbestay`
- Labels: `self-hosted`, `macOS`, `ARM64`, `rebbestay-ci`
- Docker runtime: `rebbestay-actions`
- App Quality and Database jobs historically passed
- Latest Docker evidence: zero containers, zero volumes and 12 cached Supabase
  images after job cleanup

### AIJAA

- Runner: `eden-aijaa-ci`
- Labels: `self-hosted`, `Linux`, `ARM64`, `aijaa-ci`
- Docker runtime: `aijaa-ci`
- No macOS home-directory mount was reported
- Latest push and pull-request jobs passed at AIJAA commit `23efeb8`
- Earlier detailed result: 831 passed, 41 skipped
- Ruff, JavaScript syntax, lock check, diff check, Alembic, offline SQL and
  downgrade/upgrade checks passed
- Push and PR runs passed
- `Runner.Listener` verified active inside the `aijaa-ci` VM
- Latest Docker evidence: zero containers and five unlinked anonymous volumes,
  approximately 251.5 MB total

Both runner listeners require host-permission and network review.

## Open risks

- No verified off-device backup
- Four running Colima profiles with overlapping names and responsibilities
- Five anonymous AIJAA CI volumes require ownership and cleanup classification
- `rebbestay-ci` was verified as an empty isolated AIJAA duplicate that does
  not own the macOS localhost forwards
- The Supabase-named volume in `rebbestay-ci` remains unclassified
- `rebbestay-ci` requires a reviewed stop-only observation before any
  retirement decision; deletion remains prohibited
- GitHub runner needs host-permission and network hardening
- RebbeStay Supabase development ports listen on all interfaces
- Local-agent scripts are not yet packaged as one tested service
- Lifecycle modes LIGHT / BALANCED / TESTING are not yet implemented
