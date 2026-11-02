# Current State

Updated: 2026-11-02

## Implemented

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
- Tailscale access to local interfaces

## Runtime locations

Runtime data currently lives under `~/.local-agent`.
Model data lives under `~/.ollama`.
The working installation currently lives under `~/local-agent`.

These directories are not copied wholesale into Git.

## Known limitations

- Components are still separate scripts.
- RAG does not yet cover every file type.
- Embedding refresh and deletion need stronger lifecycle handling.
- Remote control is split between Open WebUI, GitHub and local tools.
- Some system findings still require manual remediation.
