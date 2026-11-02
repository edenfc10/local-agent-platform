# Architecture

## Request flow

User interface
→ local assistant
→ local model
→ memory and retrieval
→ typed tool
→ action plan
→ exact approval
→ execution
→ audit and undo

## Knowledge

- Lexical chunks are stored in SQLite.
- Semantic vectors are generated with `embeddinggemma`.
- Retrieval is scoped to explicitly registered roots.
- File contents are treated as data, never as instructions.
- Runtime memory and embeddings remain outside Git.

## Actions

Actions use named tools with validated parameters. The model does not receive
an unrestricted shell. Changes are planned first and executed only after the
required approval text is supplied.

## Monitoring

Guardian checks CPU, memory, swap, disk, Docker, Ollama, ports, launch agents
and protected containers. Background work is restricted by battery and load.
