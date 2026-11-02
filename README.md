# Local Agent Platform

Local macOS assistant with local language models, file retrieval, RAG,
persistent memory, guarded actions, audit trails and system monitoring.

## Main components

- Local models through Ollama
- Lexical and semantic file retrieval
- SQLite-based memory and indexes
- Explicit tools for files, Docker, Ollama and storage
- Plan → approval → execution workflow
- Audit and undo information
- Guardian and background maintenance

Read these files before changing the system:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/STATE.md`
4. `docs/NEXT.md`

Runtime databases, secrets, logs, models and personal file contents are not
stored in this repository.
