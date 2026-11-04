# Home Lab Master Plan

Status: active working baseline  
Last updated: 2026-11-05 (Asia/Jerusalem)  
Evidence window: 2026-11-04 to 2026-11-05  
Operating strategy: **KEEP + IMPROVE + CONSOLIDATE**

This document is the canonical engineering plan for the Mac home lab and local
agent platform. Every infrastructure change must update this document,
`docs/STATE.md`, and `docs/NEXT.md` through a pull request.

## 1. Mission

Use the MacBook as a professional, local-first engineering platform for:

- software development and stateful local services;
- local AI through Ollama;
- RAG, persistent memory and guarded local automation;
- isolated GitHub Actions execution;
- development databases and reproducible test environments;
- Tailscale-only remote access where appropriate;
- monitoring, backup and recovery;
- low operating cost and controlled resource use.

The Mac is not the production host. Production workloads belong on external
infrastructure. The local platform is for development, CI, testing, staging,
AI and administration.

## 2. Evidence labels

All future reports and decisions use these labels:

- **VERIFIED** — observed directly during the current discovery.
- **HISTORICALLY VERIFIED** — observed previously and subject to change.
- **REPORTED** — supplied by a person or document but not independently tested.
- **NOT TESTED** — no reliable evidence yet.

A plan must not present an estimate or historical observation as current fact.

## 3. Safety and change policy

1. Read-only discovery can run without changing services.
2. Service, container, VM, network, database or GitHub changes require a
   reviewable plan.
3. Destructive actions require explicit approval, an audit record, verification
   and rollback information.
4. Running containers, registered projects and named volumes are protected.
5. Never run `docker system prune`, remove a volume, or delete a Colima profile
   as an incidental cleanup action.
6. Never commit credentials, tokens, `.env` files, runner credentials,
   personal documents, runtime databases, model weights or raw audit logs.
7. Database consolidation requires a logical backup and a successful isolated
   restore test first.
8. The `default` Colima profile is protected. RebbeStay and other active
   workloads must not be restarted or recreated as part of unrelated work.
9. Work on this repository uses a feature branch and pull request. Do not
   force-push `main`.
10. Merge only after the diff, validation and operational impact are reviewed.

## 4. Verified host inventory

### Hardware and operating system

| Item | Verified result |
| --- | --- |
| Computer | MacBook Pro, Apple Silicon M1 Max |
| Architecture | arm64 |
| CPU | 10 physical performance/efficiency cores reported by macOS |
| Unified memory | 64 GB |
| Internal storage | 1 TB SSD |
| macOS | 15.7.7, build 24G720 |
| Virtualization | Apple Virtualization.Framework through Colima |
| Docker VM mount | virtiofs |

### Resource snapshot

The discovery snapshot showed:

- CPU approximately 83% idle.
- Memory headroom approximately 80–86%.
- Swap use approximately 10.77 GB after roughly 28 days of uptime.
- Approximately 676 GiB free and 217 GiB used on the main data volume.

The swap figure is historical accumulation and does not alone prove current
memory pressure. Future decisions must use live memory pressure and sustained
CPU measurements.

### Large local storage areas

- Ollama data: approximately 56 GB.
- Colima data: historically approximately 53 GB across the profiles measured
  before the later `aijaa-ci` discovery.
- Installed Ollama model sizes are logically larger because tags can share
  blobs.
- No model was loaded during the resource audit.

These values are snapshots, not quotas or cleanup authorization.

## 5. Current Colima topology

Four profiles were observed running on 2026-11-05:

| Profile | CPU | Memory | Logical disk | Verified workload |
| --- | ---: | ---: | ---: | --- |
| `default` | 8 | 16 GiB | 120 GiB | RebbeStay, Open WebUI, FitForYou, Supabase, active AIJAA data and other development containers |
| `aijaa-ci` | 4 | 8 GiB | 60 GiB | No containers; one anonymous local volume requires classification |
| `rebbestay-actions` | 4 | 10 GiB | 60 GiB | Dedicated Docker target for the GitHub Actions runner |
| `rebbestay-ci` | 4 | 10 GiB | 60 GiB | AIJAA PostgreSQL and Redis containers plus an old Supabase-named volume |

The configured total is 20 virtual CPUs and 44 GiB of VM memory. This is not
the same as continuously consumed physical memory, but four simultaneously
running profiles create avoidable background cost and operational ambiguity.

### Protected profile: `default`

Verified services include:

- RebbeStay local Supabase stack;
- Open WebUI bound to `127.0.0.1:3000`;
- FitForYou PostgreSQL instances bound to localhost;
- AIJAA PostgreSQL and Redis;
- older AsyncML containers, mostly stopped;
- an exited Open WebUI backup container.

No consolidation work may stop, recreate or delete objects in this profile
until each workload has an owner, backup status and rollback procedure.

### `aijaa-ci`

- Running Colima VM.
- No containers.
- One anonymous volume:
  `141964a4fa7ce288aef09d9570180602279cb6ffb48158e2c4f096b6dc2838e4`.
- Volume content and size are not yet classified.
- Candidate for stop-only resource reduction after the volume is proven
  disposable or retained safely.
- Stopping is distinct from deleting; deletion is not approved.

### `rebbestay-actions`

This is the intended isolated Docker runtime for local GitHub Actions. It must
remain separate from stateful development databases. The runner itself still
executes as the normal macOS user, so Docker isolation is only partial host
isolation.

### `rebbestay-ci`

Observed containers:

- `aijaa-postgres-1`, PostgreSQL 16;
- `aijaa-redis-1`, Redis 7.

Observed volumes:

- `aijaa_postgres_data`;
- `aijaa_redis_data`;
- `supabase_db_rebbestay-true-clean.JwY3Oi`.

The AIJAA database in this profile had zero user tables during discovery.
Redis reported zero keys. The Supabase-named volume remains unclassified.
This profile is quarantined: do not delete, migrate or repurpose it until the
remaining volumes are classified.

## 6. AIJAA dependency finding

AIJAA was investigated only because duplicate code paths, databases and
profiles blocked safe infrastructure consolidation. AIJAA product development
is not the primary task of this repository.

### Code source of truth

Verified active worktree:

- Path: `~/Code/AIJAA/aijaa-reconcile`
- Repository: `edenfc10/Job-search-platform`
- Branch during the latest check: `feat/wp1-submit-safety`
- Latest observed commit:
  `3127e713f6873fcf3b9ff33861a5d272880cfc4b`
- Commit message: `ci: run checks on isolated local runner`

Historical worktree:

- `~/Code/AIJAA/aijaa`
- Branch: `feat/auth-tenancy-foundation`
- Historical commit: `c92fe7d2cd0b9865dbc9b16ae9874d78ada3edf7`

The old path `~/Downloads/AIJAA/aijaa` no longer existed, although containers
created from that historical Compose project still remained in `default`.

### Active AIJAA data

The protected `default` profile contained:

- PostgreSQL 16.15;
- database size 19,446,807 bytes during source discovery;
- 29 user tables;
- approximately 23 live rows;
- Alembic revision `6c1a9d4e2f70`;
- Redis DB size 0 with AOF enabled.

The active source tree contained 16 migrations and one head:

- Source head: `9a3c7e1f5b20`
- Required migration from the active database:
  `6c1a9d4e2f70 -> 9a3c7e1f5b20`

That migration has not been applied to the protected database.

### Verified backup and recovery evidence

A logical PostgreSQL backup was created at:

`~/Backups/AIJAA/20261104-234034/aijaa-default-postgres.dump`

SHA-256:

`affa575bcbed823c38d381ddc28976ed9d66b8272f8c56e798b346eeace876a8`

The dump was restored into an isolated temporary PostgreSQL 16 container with:

- no published ports;
- Docker network mode `none`;
- a temporary volume;
- no changes to the source database.

Restore validation succeeded:

- Alembic revision: `6c1a9d4e2f70`;
- 29 user tables;
- approximately 23 rows after analysis;
- restored database size: 9,968,663 bytes;
- temporary container and volume removed afterward.

This proves logical restorability at that point in time. It does not protect
against loss of the internal SSD because the backup is currently on the same
computer. An encrypted off-device copy remains required.

## 7. Local agent platform

### Runtime locations

- Working installation: `~/local-agent`
- Runtime state: `~/.local-agent`
- Ollama data: `~/.ollama`
- Versioned source mirror: this repository under `src/`

### Implemented capabilities

- Ollama-backed local language models;
- lexical search and scoped semantic RAG;
- `embeddinggemma` embeddings;
- SQLite memory and indexes;
- project and protected-container registry;
- disk, Docker, Ollama and project inventory;
- large-file and duplicate scanning;
- persistent plan/approval/execution actions;
- exact approval text checks;
- audit and undo metadata;
- Guardian monitoring;
- incremental background indexing;
- Tailscale-based access to selected local interfaces.

### Action boundary

The model receives typed tools, not a general unrestricted shell. Mutating
operations are expected to follow:

`discovery -> plan -> exact approval -> execution -> verification -> audit -> rollback information`

### Background services

Historically verified:

- `com.localagent.guardian`: every 300 seconds, last observed exit 0;
- `com.localagent.maintenance`: every 1,800 seconds, last observed exit 0.

They require continued load measurement and code review before being treated
as fully production-grade host agents.

## 8. GitHub Actions

Verified runner identity:

- Repository workload: RebbeStay;
- Runner: `eden-mac-rebbestay`;
- Labels: `self-hosted`, `macOS`, `ARM64`, `rebbestay-ci`;
- Installation observed under
  `~/actions-runners/rebbestay/actions-runner`;
- Runner root and `_work` observed with mode 700;
- Docker target intended to be `rebbestay-actions`;
- Runner process executes as the normal macOS user.

A RebbeStay workflow dispatch was historically verified successful for both:

- `App Quality`;
- `Database`.

Historical successful run ID: `41326112082`.

### Runner security position

Docker workloads are separated from the default development profile, but the
listener is not strongly isolated from the macOS account. Required work:

- verify the effective `DOCKER_HOST` from the active start mechanism;
- inventory read/write reachability from `_work`;
- restrict network access where practical;
- preserve the external-fork guard;
- consider a dedicated macOS account or stronger executor boundary;
- operate the CI VM on demand when possible.

Ubicloud remains an optional fallback when the Mac is unavailable. It must not
consume paid capacity by default while the local runner is available.

## 9. Network and remote access

Verified controls and findings:

- macOS application firewall enabled;
- Tailscale installed and running;
- Open WebUI bound locally and historically exposed through Tailscale Serve;
- FitForYou database ports bound to localhost;
- AIJAA PostgreSQL and Redis bound to localhost;
- RebbeStay Supabase development ports were exposed on all interfaces:
  54321, 54322, 54323, 54324 and 54327.

The Supabase bindings require remediation planning. Do not modify them while
unrelated RebbeStay work is active. The target is localhost binding with
intentional Tailscale access where remote access is required.

## 10. Backup and recovery posture

### Verified

- AIJAA logical dump exists.
- AIJAA isolated restore test succeeded.
- Dump checksum recorded.
- Runtime databases and model data are excluded from Git.

### Missing

- No Time Machine destination was found.
- No local Time Machine snapshots were found.
- No off-device copy of the AIJAA dump was verified.
- No tested restore procedure exists yet for:
  - local agent SQLite memory and indexes;
  - Open WebUI data;
  - RebbeStay/Supabase data;
  - FitForYou databases;
  - Docker volumes generally;
  - runner configuration;
  - Colima profile recreation.

Backup files may contain sensitive data. Off-device copies must be encrypted
and must never be committed to Git.

## 11. Risk register

| Priority | Risk | Current control | Required response |
| --- | --- | --- | --- |
| Critical | Internal SSD is the only verified backup location | AIJAA logical dump and restore test | Add encrypted off-device backup and recurring verification |
| High | Four Colima profiles run with overlapping purposes | Discovery inventory | Assign ownership, classify volumes, stop idle profiles, delete only after later approval |
| High | GitHub runner executes under the normal macOS user | Dedicated Docker profile and fork guard | Harden host permissions, network and account boundary |
| High | Supabase development ports listen on all interfaces | macOS firewall | Rebind locally after RebbeStay impact review |
| Medium | AIJAA source head is ahead of protected DB | Backup and tested restore | Apply migration only to an approved isolated copy first |
| Medium | Duplicate AIJAA containers and volumes | Profiles quarantined | Classify and consolidate after off-device backup |
| Medium | Ollama storage is large | Deduplicated blob storage | Add model ownership and retention policy; never remove by size alone |
| Medium | Long uptime accumulated swap | Guardian metrics | Track memory pressure and introduce lifecycle modes |
| Medium | Background scripts are not packaged as one service | launchd and audit logs | Package, test and version configuration |
| Low | Historic stopped containers create clutter | Protected inventory | Remove only after project owner and data checks |

## 12. Target architecture

### Profile model

The recommended end state is a maximum of three defined roles, with only the
necessary profiles running:

1. **Stateful development — `default`**
   - protected local databases and user-facing development services;
   - stable ports;
   - no CI jobs;
   - changes scheduled and backed up.

2. **Ephemeral CI — `rebbestay-actions`**
   - GitHub Actions Docker workloads only;
   - starts for CI/testing and can stop when idle;
   - no durable application data.

3. **Isolated testing/staging — profile to be selected**
   - one profile only;
   - temporary restored databases and migration rehearsal;
   - no production secrets;
   - starts only in TESTING mode.

The selected testing profile may reuse `aijaa-ci` after its anonymous volume
is classified. `rebbestay-ci` is not retired until its three volumes are
classified and any required data is backed up.

### Local agent service model

A single authenticated local API should eventually coordinate:

- conversation and persistent memory;
- RAG indexing and retrieval;
- typed read-only tools;
- guarded action plans;
- Guardian status;
- lifecycle mode changes;
- Tailscale-only control UI.

Runtime data stays outside Git. Schemas, migration logic, scripts, tests,
examples and operational documentation belong in Git.

### Lifecycle modes

#### LIGHT

Use when the Mac is primarily a personal workstation:

- stateful profile only when required;
- CI and isolated test profiles stopped;
- no Ollama model loaded;
- Guardian active at low frequency;
- background indexing limited by battery and load.

#### BALANCED

Use for normal development:

- required stateful services running;
- local agent and RAG available;
- Ollama loaded on demand;
- CI profile starts only when jobs are queued;
- resource alerts enabled.

#### TESTING

Use for CI, migration rehearsal and integration tests:

- isolated test profile active;
- CI profile active if required;
- explicit CPU/memory budget;
- temporary containers and volumes tracked;
- cleanup verifies that only ephemeral resources are removed;
- return to BALANCED or LIGHT after the run.

No lifecycle command may delete named volumes.

## 13. Delivery roadmap

### Phase 0 — Documentation baseline

- Merge this master plan through a PR.
- Make this document mandatory reading.
- Keep `STATE.md` and `NEXT.md` current.
- Store raw local audit reports outside Git; commit only redacted conclusions.

### Phase 1 — Protect data

- Configure an encrypted off-device backup destination.
- Copy and verify the AIJAA dump off-device.
- Add backup manifests for all stateful workloads.
- Write restore runbooks.
- Perform at least one isolated restore test per stateful service.

Exit criteria: every protected stateful service has an owner, backup,
checksum, retention rule and tested restore evidence.

### Phase 2 — Assign profile ownership

- Classify the anonymous `aijaa-ci` volume.
- Classify the three `rebbestay-ci` volumes.
- Verify the runner's actual Docker socket.
- Create a profile ownership table with allowed workloads.
- Stop empty or idle profiles only after review.
- Observe the Mac for regressions before considering deletion.

Exit criteria: every running profile has one documented role; no profile is
running without an active workload or explicit reason.

### Phase 3 — Consolidate safely

- Select one isolated testing/staging profile.
- Move no database until its backup and restore test pass.
- Rehearse AIJAA migration on a restored copy.
- Retire duplicate containers before deleting any volume.
- Keep a rollback window.

Exit criteria: target profile model reached without data loss and with
documented rollback.

### Phase 4 — Harden CI

- Verify runner environment and socket at startup.
- Restrict runner filesystem access.
- Review outbound and lateral network access.
- Add preflight and post-job cleanup checks.
- Start/stop CI capacity on demand.
- Keep cloud fallback disabled unless intentionally selected.

Exit criteria: CI is reproducible, isolated from durable data and leaves no
unexpected resources.

### Phase 5 — Harden networking

- Rebind development services to localhost where possible.
- Expose remote interfaces only through authenticated Tailscale paths.
- Baseline expected listeners.
- Alert on new public listeners without treating expected localhost forwards as
  incidents.

Exit criteria: no database or development admin interface is unintentionally
reachable from the LAN.

### Phase 6 — Productize the local agent

- Convert scripts into a package with a stable configuration schema.
- Add tests for approvals, protected targets and rollback.
- Add file adapters and embedding lifecycle handling.
- Provide one authenticated API and control interface.
- Add health, metrics and structured logs.
- Document upgrades and rollback.

## 14. Immediate prioritized tasks

1. Merge this documentation PR.
2. Complete the read-only volume-size and metadata report for
   `aijaa-ci`, `rebbestay-ci` and `rebbestay-actions`.
3. Choose and configure an encrypted off-device backup target.
4. Copy and verify the existing AIJAA dump off-device.
5. Produce a stop-only plan for confirmed idle Colima profiles.
6. Harden the GitHub runner.
7. Remediate public Supabase bindings after a RebbeStay impact review.
8. Implement lifecycle modes.

## 15. PR operating workflow

For every future change:

1. Synchronize local `main`.
2. Create a focused feature branch.
3. Record the current evidence and intended outcome.
4. Make one coherent change.
5. Run the minimum meaningful verification.
6. Update `docs/STATE.md` and `docs/NEXT.md`.
7. Open a PR containing:
   - motivation;
   - evidence;
   - exact changes;
   - validation;
   - operational impact;
   - rollback;
   - unresolved risks.
8. Review before merge.
9. After merge, update local runtime only through a separate reviewed rollout
   when the repository change affects the machine.

Documentation in Git does not itself authorize a runtime mutation.
