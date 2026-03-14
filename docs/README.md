# Terraform Generator Service — Documentation Index

This folder contains the project documentation for the Terraform Generator Service, following a Prompt-Driven Development (PDD) approach.

---

## Core Documents

| Document | Purpose |
|----------|---------|
| [PDD.md](./PDD.md) | **Prompt-Driven Development Document** — Full specification: architecture, domain model, events, JSON Schema, Terraform generation, risks, roadmap |
| [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md) | **Artifact Storage** — Environment-based: local (dev) or Cloudflare upload (production); directory per job |
| [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) | Concise roadmap, phase dependencies, milestones, suggested first feature |
| [DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md) | Actionable checklist with checkboxes for tracking implementation progress |
| [PROMPT_GUIDE.md](./PROMPT_GUIDE.md) | Guide for future Cursor prompts — feature-specific prompt templates, constraints, implementation order |

---

## Quick Links

- **First feature to implement:** JSON Ingestion + Validation → [IMPLEMENTATION_ROADMAP.md#suggested-first-feature](./IMPLEMENTATION_ROADMAP.md#suggested-first-feature-to-implement)
- **V1 scope:** [PDD.md#v1-scope](./PDD.md#v1-scope)
- **Out of scope:** [PDD.md#out-of-scope](./PDD.md#out-of-scope)
- **Event names:** [PDD.md#event-naming-convention](./PDD.md#event-naming-convention)
- **Folder structure:** [PDD.md#suggested-folder-structure](./PDD.md#suggested-folder-structure)
- **Artifact storage:** [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md)

---

## Schemas

- **Input schema:** `../schemas/input_v1.json` — Validates incoming JSON (`analise_entrada`, vibes, recursos)
- **Domain schema:** `../schemas/architecture_v1.json` — Validates the normalized architecture output

---

## Reading Order for New Implementers

1. [PDD.md](./PDD.md) — Overview, Objective, Architecture, Domain Model
2. [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) — Phases and first feature
3. [PROMPT_GUIDE.md](./PROMPT_GUIDE.md) — How to implement feature-by-feature
4. [DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md) — Track progress
