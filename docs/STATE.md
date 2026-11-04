# Current State

Updated: 2026-11-05

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
- Approximately 676 GiB free during discovery
- CPU approximately 83% idle during the main snapshot
- Four running Colima profiles:
  - `default`: 8 CPU / 16 GiB / 120 GiB logical disk
  - `aijaa-ci`: 4 CPU / 8 GiB / 60 GiB
  - `rebbestay-actions`: 4 CPU / 10 GiB / 60 GiB
  - `rebbestay-ci`: 4 CPU / 10 GiB / 60 GiB
- Ollama data approximately 56 GB; no model loaded during the audit
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
- Latest reported HEAD: `6aca9ec` — `ci: install Node.js on local runner`
- Earlier verified commit:
  `3127e713f6873fcf3b9ff33861a5d272880cfc4b`
- Protected database revision: `6c1a9d4e2f70`
- Source migration head: `9a3c7e1f5b20`
- One migration is pending on the protected database
- Logical backup created under `~/Backups/AIJAA/20261104-234034`
- Backup SHA-256:
  `affa575bcbed823c38d381ddc28976ed9d66b8272f8c56e798b346eeace876a8`
- Isolated restore succeeded with 29 tables and approximately 23 rows
- No migration was applied to the protected database
- No off-device copy has been verified

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
- CI result: 831 passed, 41 skipped
- Ruff, JavaScript syntax, lock check, diff check, Alembic, offline SQL and
  downgrade/upgrade checks passed
- Push and PR runs passed
- Latest Docker evidence: zero containers and two unlinked anonymous volumes
  of approximately 50 MB each

Both runner listeners require host-permission and network review.

## Open risks

- No verified off-device backup
- Four running Colima profiles with overlapping names and responsibilities
- Two anonymous AIJAA CI volumes require ownership and cleanup classification
- Three volumes in `rebbestay-ci` require final classification
- `rebbestay-ci` is reported as the current AIJAA local server; its logical
  state must be refreshed before consolidation
- GitHub runner needs host-permission and network hardening
- RebbeStay Supabase development ports listen on all interfaces
- Local-agent scripts are not yet packaged as one tested service
- Lifecycle modes LIGHT / BALANCED / TESTING are not yet implemented
