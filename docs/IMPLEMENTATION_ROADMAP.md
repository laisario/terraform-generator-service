# Implementation Roadmap

**Service:** Terraform Generator Service  
**Reference:** [PDD.md](./PDD.md)

---

## Concise Implementation Roadmap

```
Phase 1: Foundation        →  Domain models, schema, config, project setup
Phase 2: Parsing           →  Markdown → structured blocks
Phase 3: Extraction       →  Blocks → raw requirements
Phase 4: Normalization     →  Raw → domain model + dependency resolution
Phase 5: Validation        →  JSON Schema + custom rules
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
    ├──► Phase 2 (Parsing) ──► Phase 3 (Extraction)
    │                              │
    │                              ▼
    │                         Phase 4 (Normalization)
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
| **M1: Foundation** | Project runs, domain + schema exist | `python -m terraform_generator --help` works; schema validates sample JSON |
| **M2: Parse** | Markdown → blocks | Unit test: sample MD → list of blocks with headings/code |
| **M3: Extract** | Blocks → raw requirements | Unit test: HCL block → raw resource record |
| **M4: Normalize** | Raw → domain model | Unit test: raw records → `Architecture` with resolved deps |
| **M5: Validate** | Schema + rules | Unit test: valid/invalid models → correct pass/fail |
| **M6: Generate** | Terraform files | Unit test: domain model → correct `.tf` output |
| **M7: Pipeline** | End-to-end sync | Integration test: MD file → Terraform files on disk |
| **M8: Event Bus** | Async processing | Consumer processes `ingest.requested` → emits `completed` |

---

## Suggested First Feature to Implement

**Feature:** *Markdown Ingestion + Parsing to Structured Blocks*

**Why first:**
- No dependencies on extraction, normalization, or Terraform
- Validates project setup and domain boundaries
- Produces a concrete, testable output (blocks)
- Unblocks extraction (Phase 3)

**Scope:**
1. Project setup (`pyproject.toml`, `src/terraform_generator`, ruff)
2. `ingestion.loader`: Load Markdown from file path or string
3. `parsing.markdown_parser`: Parse MD to list of blocks (Heading, CodeBlock)
4. Unit tests: given `sample.md`, assert block types and content

**Acceptance criteria:**
- [ ] `Loader.load_from_path("architectures/sample.md")` returns raw Markdown string
- [ ] `MarkdownParser.parse(md)` returns `List[Block]` with correct `BlockType` and content
- [ ] Code block with `terraform` language is correctly identified

**Sample input for first feature:**

```markdown
# My Architecture

## S3

```terraform
resource "aws_s3_bucket" "main" {
  bucket = "my-bucket"
}
```
```

**Expected parsed output (conceptual):**
- Block 1: Heading(level=1, text="My Architecture")
- Block 2: Heading(level=2, text="S3")
- Block 3: CodeBlock(lang="terraform", content="resource \"aws_s3_bucket\" ...")

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
- [ ] Sample architecture fixture (e.g., tests/fixtures/sample_architectures/web_app.md)

### Definition of Done
- End-to-end: Markdown file in → Terraform files out
- All six V1 AWS resource types supported
- JSON Schema validation enforced
- No Terraform execution
