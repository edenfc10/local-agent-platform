# Next Work

Updated: 2026-11-06

The ordered roadmap and exit criteria are maintained in
`docs/HOME_LAB_MASTER_PLAN.md`.

## P0 — Establish the operating baseline

Status: complete.

1. Home Lab Master Plan merged through PR #1.
2. Future infrastructure changes use feature branches and pull requests.
3. `HOME_LAB_MASTER_PLAN.md`, `STATE.md` and `NEXT.md` remain synchronized.

## P1 — Protect state

Status: foundation proposed; live backup actions are not authorized.

Completed in the foundation PR:

1. Define protected workloads and provisional recovery objectives.
2. Define backup tiers, retention, encryption and restore-proof requirements.
3. Add a read-only backup destination preflight.
4. Add a non-mutating SHA-256 manifest verifier.
5. Record the verified AIJAA local backup and isolated restore evidence.

Next execution steps:

1. Run the read-only iCloud Drive preflight.
2. Define secure password/recovery-key handling outside the backup.
3. Create a client-side encrypted copy of the verified AIJAA backup under an
   approved execution plan.
4. Verify iCloud synchronization, download and destination checksum.
5. Inventory every remaining stateful database and named Docker volume.
6. Write and test restore runbooks for local-agent memory, RebbeStay,
   FitForYou and Open WebUI.
7. Confirm RPO and RTO targets from real change frequency and restore duration.
8. Add reviewed retention cleanup only after two usable copies exist.

## P2 — Consolidate Colima safely

Completed evidence:

1. Measured physical and logical storage for all four profiles.
2. Verified that macOS AIJAA localhost forwarding belongs to `default`.
3. Compared both AIJAA PostgreSQL clusters and Redis instances.
4. Classified `rebbestay-ci` as an empty isolated duplicate candidate.
5. Verified the RebbeStay listener on macOS and the AIJAA listener inside its
   VM.

Next execution steps:

1. Prepare a persistent stop-only plan for `rebbestay-ci`.
2. Preserve every container, image and volume.
3. Stop only the `rebbestay-ci` VM after explicit approval.
4. Verify AIJAA PostgreSQL and Redis on localhost remain healthy.
5. Observe for regressions before considering retirement.
6. Classify the Supabase-named volume in `rebbestay-ci`.
7. Classify the five anonymous `aijaa-ci` volumes (251.5 MB total).
8. Add stop-only, on-demand lifecycle plans for both CI profiles.
9. Do not delete any profile or volume until encrypted off-device recovery is
   proven.


## P3 — Harden GitHub Actions

1. Verify the effective Docker socket for both runners at startup.
2. Inventory filesystem read/write access for both runner work directories.
3. Preserve the AIJAA runner's no-home-mount boundary.
4. Restrict network access where practical.
5. Add job preflight and post-job cleanup verification.
6. Add safe handling for orphaned anonymous CI volumes.
7. Keep external-fork guards.
8. Evaluate dedicated macOS users or stronger executor boundaries.
9. Start both CI profiles on demand where reliable.
10. Upgrade `actions/setup-node` v4 to v6 in a separate maintenance PR.

## P4 — Harden networking

1. Review RebbeStay impact before changing Supabase bindings.
2. Bind databases and development admin interfaces to localhost.
3. Use authenticated Tailscale routes for intentional remote access.
4. Baseline expected listeners and alert on unexpected public listeners.

## P5 — Add lifecycle modes

1. Implement LIGHT mode.
2. Implement BALANCED mode.
3. Implement TESTING mode.
4. Prohibit volume deletion from lifecycle transitions.
5. Record state transitions and verification in the audit log.

## P6 — Productize the local agent

1. Define a package layout and configuration schema.
2. Add tests for approval boundaries and protected targets.
3. Add incremental file watching and embedding lifecycle management.
4. Add document adapters for PDF, Word and CSV.
5. Create one API service for assistant, memory, RAG and tools.
6. Build one authenticated Tailscale-only control interface.
7. Add backup and restore procedures for configuration and memory.
8. Add health checks, metrics, structured logs and upgrade rollback.
