# Agent Instructions

Before making changes:

1. Read `docs/HOME_LAB_MASTER_PLAN.md`.
2. Read `docs/ARCHITECTURE.md`.
3. Read `docs/STATE.md`.
4. Read `docs/NEXT.md`.
5. Inspect the current Git branch, HEAD and working tree.
6. Classify important claims as VERIFIED, HISTORICALLY VERIFIED, REPORTED or
   NOT TESTED.
7. Never commit credentials, tokens, `.env` files, personal documents,
   runtime databases, indexes, raw audit logs, backups or model weights.
8. Read-only tools may run automatically.
9. File changes must have a reviewable diff.
10. Destructive or service-changing actions require a persistent plan,
    explicit approval, audit entry, verification and rollback information.
11. Running containers, named volumes, registered projects and the Colima
    `default` profile are protected.
12. A backup is not considered verified until an isolated restore succeeds.
13. Documentation does not authorize a runtime mutation.
14. Update `docs/HOME_LAB_MASTER_PLAN.md`, `docs/STATE.md` and
    `docs/NEXT.md` when architecture, ownership, risks or priorities change.

## Git workflow

- Use a dedicated feature branch.
- Open a pull request for every coherent change.
- Include motivation, evidence, validation, operational impact, rollback and
  unresolved risks in the PR.
- Do not force-push `main`.
- Do not merge or deploy without review.
