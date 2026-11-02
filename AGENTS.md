# Agent Instructions

Before making changes:

1. Read `docs/ARCHITECTURE.md`.
2. Read `docs/STATE.md`.
3. Read `docs/NEXT.md`.
4. Inspect the current Git branch and working tree.
5. Never commit credentials, tokens, `.env` files, personal documents,
   runtime databases, indexes, logs or model weights.
6. Read-only tools may run automatically.
7. File changes must have a reviewable diff.
8. Destructive or service-changing actions require a persistent plan,
   explicit approval, audit entry and rollback information.
9. Running containers and registered project paths are protected.
10. Update `docs/STATE.md` and `docs/NEXT.md` with every architectural change.

Use a dedicated feature branch. Never force-push `main`.
