# Next Work

Updated: 2026-11-05

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

1. Connect the selected external SSD and identify its mount path.
2. Run the read-only preflight to verify encrypted APFS, capacity and that it
   is on a different filesystem from the internal SSD.
3. Copy the verified AIJAA dump off-device under an approved execution plan.
4. Verify the destination checksum.
5. Inventory every remaining stateful database and named Docker volume.
6. Write and test restore runbooks for local-agent memory, RebbeStay,
   FitForYou and Open WebUI.
7. Confirm RPO and RTO targets from real change frequency and restore duration.
8. Add reviewed retention cleanup only after two usable copies exist.

## P2 — Consolidate Colima safely

1. Treat the profile size and metadata report as completed.
2. Classify the two anonymous `aijaa-ci` volumes left by CI.
3. Refresh the logical database and Redis state in `rebbestay-ci`.
4. Classify the Supabase-named volume in `rebbestay-ci`.
5. Record explicit ownership:
   - `default`: protected stateful development
   - `rebbestay-actions`: RebbeStay CI
   - `aijaa-ci`: AIJAA CI
   - `rebbestay-ci`: current AIJAA local runtime
6. Add stop-only, on-demand lifecycle plans for both CI profiles.
7. Observe before proposing any deletion or profile rename.

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
