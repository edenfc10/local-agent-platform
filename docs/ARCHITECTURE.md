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
+-- Colima: rebbestay-actions [RebbeStay CI]
|   +-- runner: eden-mac-rebbestay
|   +-- ephemeral Supabase test workloads
|
+-- Colima: aijaa-ci [AIJAA CI]
|   +-- runner: eden-aijaa-ci
|   +-- ephemeral PostgreSQL test workloads
|   +-- no macOS home mount
|
+-- Colima: rebbestay-ci [AIJAA local runtime; name under review]
    +-- AIJAA PostgreSQL and Redis
    +-- unclassified Supabase-named volume
```

## Target profile roles

1. `default`: protected shared stateful development.
2. `rebbestay-actions`: RebbeStay CI, active on demand.
3. `aijaa-ci`: AIJAA CI, active on demand.
4. `rebbestay-ci`: current AIJAA local database runtime, pending a later
   reviewed rename or consolidation.

Project-specific CI profiles remain separated. Resource savings come from
safe on-demand lifecycle control. No profile or volume is deleted as part of
a lifecycle transition.

## External boundaries

- The Mac is not the production server.
- Remote interfaces use authenticated Tailscale access.
- GitHub coordinates CI, while local or cloud runners execute jobs.
- Ubicloud is optional fallback capacity rather than the default runner.
- Secrets, databases, backups and model weights remain outside Git.
