# Backup and Recovery Foundation

Status: proposed baseline  
Updated: 2026-11-05  
Scope: Mac home lab, local agent, development databases and local CI state

This document defines the minimum recovery standard for protected local
workloads. It does not authorize a backup, restore, database migration, service
restart, container recreation or volume deletion.

## 1. Objectives

The backup system must:

- prevent loss of important state when the Mac or its internal SSD fails;
- keep credentials and personal data out of Git;
- produce checksummed, timestamped and reviewable backup sets;
- prove recovery with isolated restore tests;
- avoid changing live services during inventory and verification;
- define ownership, retention and recovery expectations for every workload;
- support low-cost operation before introducing paid infrastructure.

A backup on the same internal SSD is a recovery artifact, but it is not an
off-device backup.

## 2. Evidence model

Use the repository evidence labels:

- **VERIFIED** — observed directly during the current work.
- **HISTORICALLY VERIFIED** — observed earlier and may have changed.
- **REPORTED** — supplied by a person or another report.
- **NOT TESTED** — not validated.

A workload is marked **restore-verified** only after an isolated restore
completes and expected structural checks pass. A checksum or archive listing
alone is insufficient.

## 3. Current recovery evidence

### AIJAA PostgreSQL

| Field | Value | Evidence |
|---|---|---|
| Source profile | `default` | VERIFIED |
| Source container | `aijaa-postgres-1` | VERIFIED |
| Source revision | `6c1a9d4e2f70` | VERIFIED |
| Source tables | 29 | VERIFIED |
| Logical dump | `~/Backups/AIJAA/20261104-234034/aijaa-default-postgres.dump` | VERIFIED |
| SHA-256 | `affa575bcbed823c38d381ddc28976ed9d66b8272f8c56e798b346eeace876a8` | VERIFIED |
| Isolated restore | succeeded without published ports | VERIFIED |
| Restored revision | `6c1a9d4e2f70` | VERIFIED |
| Restored tables | 29 | VERIFIED |
| Off-device copy | none verified | NOT TESTED |

The logical dump is recoverable, but it remains exposed to loss of the Mac or
its internal SSD until a second copy is stored on an encrypted device or
encrypted remote destination.

### Other workloads

No other workload is yet considered restore-verified under this policy.

## 4. Protected workload inventory

| Workload | Stateful source | Required backup | Current status | Initial recovery target |
|---|---|---|---|---|
| AIJAA PostgreSQL | protected named volume in `default` | logical dump plus metadata | restore-verified locally; off-device copy missing | 4 hours |
| AIJAA Redis | named Redis volume | classify persistence need first | latest DBSIZE was 0 | best effort |
| RebbeStay Supabase | PostgreSQL and Supabase volumes in `default` | logical database backup plus storage inventory | NOT TESTED | 4 hours |
| FitForYou databases | PostgreSQL volumes in `default` | logical dump per database | NOT TESTED | 8 hours |
| Open WebUI | `open-webui` volume | application data export or volume-safe backup | NOT TESTED | 8 hours |
| Local-agent memory | `~/.local-agent` SQLite and configuration | SQLite-safe copy, configuration manifest | NOT TESTED | 4 hours |
| Local-agent source | this Git repository | Git remote | versioned | 1 hour |
| Ollama models | `~/.ollama` | normally reproducible manifest, not full model backup | NOT TESTED | 24 hours |
| CI runners | runner registration and local configuration | rebuild runbook; never store credentials in Git | NOT TESTED | 4 hours |
| Colima configuration | profile metadata and intended resource settings | sanitized configuration inventory | partially documented | 8 hours |

Recovery targets are provisional engineering objectives. They are not service
level agreements.

## 5. Backup tiers

### Tier 0 — Reproducible

Source code, dependency locks, infrastructure documentation and public model
identifiers should be reproducible from Git and package registries.

### Tier 1 — Local recovery artifact

Timestamped dumps or application-safe copies may be created on the internal
SSD for fast recovery and restore testing. This tier does not protect against
device loss or internal SSD failure.

### Tier 2 — Encrypted off-device copy

Every protected stateful workload must have at least one encrypted copy outside
the internal SSD. Acceptable destinations include:

- an encrypted APFS external SSD;
- an encrypted Time Machine destination with successful backup evidence;
- client-side encrypted cloud storage.

No external SSD is currently available (**REPORTED**, 2026-11-05). The only
known backup location is the Mac's internal SSD, so off-device protection
remains unresolved. A client-side encrypted copy in an existing cloud account
is the preferred temporary option if acceptable; purchasing storage is not
authorized by this document.

### Tier 3 — Independent second copy

For data that would be expensive or impossible to recreate, keep another copy
with a different failure mode, such as an encrypted external SSD plus
client-side encrypted cloud storage.

## 6. Backup set structure

Each backup set should use a timestamped directory:

```text
<destination>/<workload>/<YYYYMMDD-HHMMSS>/
├── README.txt
├── MANIFEST.sha256
├── inventory.json
├── backup artifact(s)
└── restore-evidence/
```

The metadata must record:

- workload and owning project;
- creation timestamp and timezone;
- source profile, container or application;
- source Git repository, branch and commit when applicable;
- schema or migration revision;
- backup command family, without secret values;
- artifact sizes and checksums;
- restore test date and outcome;
- retention class;
- known limitations.

Do not record passwords, tokens, connection strings, raw environment values or
personal records.

## 7. Retention baseline

Until workload-specific data growth is measured:

- keep 7 daily backup sets;
- keep 4 weekly backup sets;
- keep 3 monthly backup sets;
- retain the latest restore-verified set until a newer set passes restore;
- never prune the only off-device copy;
- require a reviewed plan before deletion.

Retention must be adjusted for available capacity and data sensitivity. Backup
pruning is a mutating operation and is outside the scope of verification
scripts in this repository.

## 8. Encryption and access

- External media must use encrypted APFS or encrypted Time Machine.
- Cloud copies must be encrypted before upload when provider-side access is not
  acceptable.
- Encryption keys must not be committed to Git or stored beside the only copy.
- Backup directories should be private to the owning macOS user.
- Runner jobs must not receive access to backup destinations.
- Backups must not be mounted into CI containers.
- Restore tests must use isolated containers or temporary volumes with no
  published ports unless a reviewed runbook requires otherwise.

## 9. Restore proof

A restore test should verify, as applicable:

1. artifact checksum;
2. archive or dump structure;
3. isolated target creation;
4. successful restore without using production credentials;
5. expected schema or migration revision;
6. expected table/object counts;
7. application-level health or read-only query;
8. removal of temporary resources;
9. confirmation that the source was unchanged;
10. evidence log without secret values.

A restore test that only opens an archive does not prove application recovery.

## 10. RPO and RTO baseline

| Class | Example | Provisional RPO | Provisional RTO |
|---|---|---:|---:|
| A — irreplaceable state | active project databases, local-agent memory | 24 hours | 4 hours |
| B — important state | Open WebUI data, development databases | 7 days | 8 hours |
| C — reproducible cache | Ollama models, CI images and caches | rebuild | 24 hours |

RPO is maximum acceptable data loss. RTO is the target time to restore useful
service. These values need confirmation after actual data-change frequency and
restore duration are measured.

## 11. Operating workflow

Every workload follows:

1. read-only inventory;
2. reviewed backup plan;
3. backup creation;
4. checksum and manifest creation;
5. encrypted off-device copy;
6. checksum verification at destination;
7. isolated restore test;
8. evidence update in `docs/STATE.md`;
9. retention review;
10. separate reviewed cleanup, if needed.

## 12. Verification tools

- `scripts/backup_preflight.sh` performs a read-only preflight for a proposed
  destination and known source paths. It does not copy data.
- `scripts/verify_backup_manifest.sh` validates a SHA-256 manifest. It does
  not restore or delete data.

Both scripts intentionally avoid reading environment values, database records,
runner credentials and backup contents.

## 13. Decisions still required

Before copying a backup off-device:

1. select an available off-device destination: client-side encrypted cloud
   storage now, or an encrypted external SSD later;
2. verify destination capacity and access without exposing credentials;
3. decide how the encryption or recovery key is retained away from the backup;
4. decide whether a second independent copy is required later;
5. confirm acceptable RPO for each active project;
6. identify who authorizes and records retention cleanup.

## 14. Exit criteria for P1

P1 is complete when:

- every stateful workload has an owner and backup method;
- at least one encrypted off-device destination is active;
- the verified AIJAA dump exists there and its checksum matches;
- critical workloads have restore runbooks;
- at least AIJAA and local-agent memory pass isolated restore tests;
- retention rules are recorded and a safe pruning workflow exists;
- evidence is updated through reviewed pull requests.
