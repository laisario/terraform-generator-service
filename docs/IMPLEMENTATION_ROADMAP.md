# Implementation Roadmap

**Service:** Terraform Generator Service  
**Reference:** [PDD.md](./PDD.md)

---

## Concise Implementation Roadmap

```
Phase 1: Foundation        →  Domain models, schemas (input + domain), config, project setup
Phase 2: JSON Ingestion    →  Load JSON, validate against input_v1.json
Phase 3: Service Analysis  →  Analyze recursos; map servico/config to resource list
Phase 4: Normalization     →  Analyzed resources → domain model + dependency resolution
Phase 5: Validation        →  Domain JSON Schema + custom rules
Phase 6: Terraform Gen     →  Templates, selector, generator, writer
Phase 7: Pipeline          →  Synchronous orchestration (no broker)
Phase 8: Event Bus (opt)   →  Redis/RabbitMQ consumer + publisher
Phase 9: Polish            →  Tests, docs, samples
```

**Estimated total:** 6–7 weeks for full V1 (Phases 1–7). Phase 8 is optional for V1 if sync API is sufficient.

---

## Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├──► Phase 2 (JSON Ingestion) ──► Phase 3 (Service Analysis)
    │                                      │
    │                                      ▼
    │                                 Phase 4 (Normalization)
    │                              │
    │                              ▼
    │                         Phase 5 (Validation)
    │                              │
    └──────────────────────────────┼──────────────────► Phase 6 (Terraform Gen)
                                   │                              │
                                   └──────────────────────────────┼──► Phase 7 (Pipeline)
                                                                   │
                                                                   └──► Phase 8 (Event Bus)
                                                                              │
                                                                              └──► Phase 9 (Polish)
```

---

## Milestone Definitions

| Milestone | Deliverable | Definition of Done |
|-----------|-------------|--------------------|
| **M1: Foundation** | Project runs, domain + schemas exist | `python -m terraform_generator --help` works; input + domain schemas validate sample JSON |
| **M2: JSON Ingestion** | JSON load + validate | Unit test: sample JSON → validated payload; invalid JSON → clear error |
| **M3: Service Analysis** | Recursos → resource list | Unit test: JSON with recursos → analyzed resource list |
| **M4: Normalize** | Analyzed → domain model | Unit test: analyzed resources → `Architecture` with resolved deps |
| **M5: Validate** | Schema + rules | Unit test: valid/invalid models → correct pass/fail |
| **M6: Generate** | Terraform files | Unit test: domain model → correct `.tf` output |
| **M7: Pipeline** | End-to-end sync | Integration test: JSON file → Terraform files on disk |
| **M8: Event Bus** | Async processing | Consumer processes `ingest.requested` → emits `completed` |

---

## Suggested First Feature to Implement

**Feature:** *JSON Ingestion + Input Validation*

**Why first:**
- No dependencies on service analysis, normalization, or Terraform
- Validates project setup and input contract
- Produces a concrete, testable output (validated payload)
- Unblocks service analysis (Phase 3)

**Scope:**
1. Project setup (`pyproject.toml`, `src/terraform_generator`, ruff)
2. `ingestion.loader`: Load JSON from file path or string
3. `input.validator`: Validate against `schemas/input_v1.json`
4. Unit tests: given `sample_inputs/web_app.json`, assert validation passes; given invalid JSON, assert clear error

**Acceptance criteria:**
- [ ] `Loader.load_from_path("fixtures/sample_inputs/web_app.json")` returns parsed JSON dict
- [ ] `InputValidator.validate(data)` returns validated payload when structure is correct
- [ ] Invalid JSON (missing `analise_entrada`, malformed `recursos`) raises validation error with clear message

**Sample input for first feature:** See `tests/fixtures/sample_inputs/web_app.json`

**Expected validated output (conceptual):**
- `analise_entrada` present
- `vibe_economica.recursos` and/or `vibe_performance.recursos` as list of `{servico, config}` objects

---

## Quick Reference: Event Names

| Event | Purpose |
|-------|---------|
| `architecture.ingest.requested` | Trigger pipeline |
| `architecture.parsed` | Parsing done |
| `architecture.extracted` | Extraction done |
| `architecture.normalized` | Normalization done |
| `architecture.validated` | Validation done |
| `architecture.templates.selected` | Template selection done |
| `architecture.terraform.generated` | Generation done |
| `architecture.processing.completed` | Success |
| `architecture.processing.failed` | Failure |

---

## Quick Reference: V1 AWS Resource Types

- `aws_s3_bucket`
- `aws_s3_bucket_versioning`
- `aws_instance`
- `aws_security_group`
- `aws_vpc`
- `aws_subnet`

---

## Final Deliverables (V1 Complete)

When V1 is complete, the following artifacts should exist:

### Documentation
- [x] PDD.md — Full specification
- [x] IMPLEMENTATION_ROADMAP.md — Phases and milestones
- [x] DEVELOPMENT_CHECKLIST.md — Implementation checklist
- [x] PROMPT_GUIDE.md — Feature implementation prompts
- [x] docs/README.md — Documentation index

### Schema
- [x] schemas/architecture_v1.json — JSON Schema for normalized output

### Code (To Be Implemented)
- [ ] src/terraform_generator/ — Python package with all stages
- [ ] templates/terraform/aws/ — Jinja2 templates for V1 resource types
- [ ] tests/ — Unit and integration tests
- [ ] Sample input fixtures (e.g., tests/fixtures/sample_inputs/web_app.json)

### Definition of Done
- End-to-end: JSON file in → Terraform files out
- All six V1 AWS resource types supported
- JSON Schema validation enforced
- No Terraform execution
