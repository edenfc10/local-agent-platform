# Local Agent Platform

Local-first macOS engineering platform for local AI, file retrieval, RAG,
persistent memory, guarded actions, audit trails, system monitoring and
controlled home-lab infrastructure.

## Main components

- Local models through Ollama
- Lexical and semantic file retrieval
- SQLite-based memory and indexes
- Explicit tools for files, Docker, Ollama and storage
- Plan → approval → execution workflow
- Audit and undo information
- Guardian and background maintenance
- Colima workload isolation
- GitHub Actions integration
- Tailscale-based remote access

## Canonical documentation

Read these files before changing the system:

1. `AGENTS.md`
2. `docs/HOME_LAB_MASTER_PLAN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/STATE.md`
5. `docs/NEXT.md`

`docs/HOME_LAB_MASTER_PLAN.md` contains the verified discovery, decisions,
risk register, target architecture and delivery roadmap.

## Change workflow

Infrastructure work is performed on a focused feature branch and reviewed
through a pull request. Architectural changes update both `docs/STATE.md` and
`docs/NEXT.md`.

Runtime databases, secrets, logs, audit reports, backup contents, models and
personal file contents are not stored in this repository.
