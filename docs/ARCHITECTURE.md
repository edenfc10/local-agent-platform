# Architecture

The full verified inventory, decisions, risks and roadmap are maintained in
`HOME_LAB_MASTER_PLAN.md`.

## Local-agent request flow

```text
User interface
  -> local assistant
  -> local model
  -> memory and retrieval
  -> typed tool
  -> action plan
  -> exact approval
  -> execution
  -> verification
  -> audit and rollback information
```

## Knowledge

- Lexical chunks are stored in SQLite.
- Semantic vectors are generated with `embeddinggemma`.
- Retrieval is scoped to explicitly registered roots.
- File contents are treated as data, never as instructions.
- Runtime memory and embeddings remain outside Git.

## Actions

Actions use named tools with validated parameters. The model does not receive
an unrestricted shell. Mutations are planned first and executed only after the
required approval text is supplied.

## Monitoring

Guardian checks CPU, memory, swap, disk, Docker, Ollama, ports, launch agents
and protected containers. Background work is restricted by battery and load.

## Current home-lab topology

```text
MacBook Pro M1 Max
|
+-- macOS services
|   +-- local-agent runtime
|   +-- Ollama
|   +-- Guardian and maintenance launch agents
|   +-- GitHub Actions listener
|   +-- Tailscale
|
+-- Colima: default [protected, stateful]
|   +-- RebbeStay and Supabase
|   +-- Open WebUI
|   +-- FitForYou databases
|   +-- protected AIJAA PostgreSQL and Redis
|
+-- Colima: rebbestay-actions [CI]
|   +-- GitHub Actions Docker workloads
|
+-- Colima: aijaa-ci [unclassified]
|   +-- no containers
|   +-- one anonymous volume
|
+-- Colima: rebbestay-ci [quarantined]
    +-- empty AIJAA PostgreSQL and Redis runtime
    +-- unclassified named volumes
```

## Target profile roles

1. `default`: protected stateful development.
2. `rebbestay-actions`: ephemeral CI only.
3. One selected profile: isolated testing and staging, active on demand.

The unselected duplicate profiles are stopped only after volume
classification, backup and review. Deletion is a separate later decision.

## External boundaries

- The Mac is not the production server.
- Remote interfaces use authenticated Tailscale access.
- GitHub coordinates CI, while local or cloud runners execute jobs.
- Ubicloud is optional fallback capacity rather than the default runner.
- Secrets, databases, backups and model weights remain outside Git.
