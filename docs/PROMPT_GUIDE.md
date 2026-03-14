# Prompt Guide for Implementation

**Purpose:** This guide helps future Cursor prompts implement the Terraform Generator Service feature-by-feature without losing architectural consistency.

**Reference documents:** [PDD.md](./PDD.md), [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md), [DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md)

---

## How to Use This Guide

When implementing a feature, **cite the relevant PDD section** and follow the prescribed structure. Do not invent new patterns that conflict with the documented architecture.

---

## Recommended Implementation Order

1. **Foundation** — Domain models, schema, config (Phase 1)
2. **Ingestion + Parsing** — First feature (see below)
3. **Extraction** — Raw requirements from blocks
4. **Normalization** — Domain model + dependency resolution
5. **Validation** — JSON Schema + custom rules
6. **Terraform Generation** — Templates, selector, generator
7. **Pipeline** — Synchronous orchestration
8. **Event Bus** — Optional; defer if sync API suffices

---

## Suggested First Feature to Implement

**Feature:** *Markdown Ingestion + Parsing to Structured Blocks*

**Prompt template:**

```
Implement the Markdown ingestion and parsing stage for the Terraform Generator Service.

Reference: docs/PDD.md (Architecture, Parsing, Markdown Input Patterns)
Reference: docs/IMPLEMENTATION_ROADMAP.md (Suggested First Feature)

Requirements:
1. Create ingestion/loader.py: load Markdown from file path or string
2. Create parsing/markdown_parser.py: parse MD to list of blocks (Heading, CodeBlock)
3. Define parsing/blocks.py: Block types (Heading, CodeBlock) with level/lang/content
4. Use markdown-it-py or mistune for parsing
5. Add unit tests in tests/unit/test_parsing.py

Acceptance criteria:
- Loader.load_from_path("path/to/file.md") returns raw Markdown string
- MarkdownParser.parse(md) returns List[Block] with correct BlockType and content
- Code block with "terraform" language is correctly identified

Sample input: See PDD "Example 1: Code Block Style"
```

---

## Feature-Specific Prompt Templates

### Extraction

```
Implement the extraction stage for the Terraform Generator Service.

Reference: docs/PDD.md (Extraction, Markdown Input Patterns)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 3)

Requirements:
1. Create extraction/extractor.py: extract raw requirements from parsed blocks
2. Detect terraform/hcl code blocks
3. Parse resource "type" "name" pattern and attributes
4. Produce raw requirement records (type, logical_name, attributes)
5. Add extraction/patterns.py for regex/pattern definitions
6. Add unit tests in tests/unit/test_extraction.py

V1 focus: HCL code block style only. Do not implement list-style extraction yet.
```

### Normalization

```
Implement the normalization stage for the Terraform Generator Service.

Reference: docs/PDD.md (Domain Model, Normalization)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 4)

Requirements:
1. Create normalization/normalizer.py: map raw records to InfrastructureResource
2. Create normalization/resolver.py: resolve dependencies, detect circular deps
3. Build Architecture root with metadata
4. Use domain models from domain/models.py
5. Add unit tests in tests/unit/test_normalization.py

Ensure: Domain model is provider-aware but template-agnostic.
```

### Validation

```
Implement the validation stage for the Terraform Generator Service.

Reference: docs/PDD.md (JSON Schema Strategy, Validation Rules)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 4)

Requirements:
1. Create validation/validator.py: JSON Schema validation + custom rules
2. Create validation/rules.py: circular deps, undefined refs, duplicate logical names
3. Use jsonschema library; schema at schemas/architecture_v1.json
4. Return ValidationResult with errors (blocking) and warnings (non-blocking)
5. Add unit tests in tests/unit/test_validation.py

Error codes: resource_type_unsupported, missing_required_attribute, circular_dependency, undefined_dependency, duplicate_logical_name
```

### Terraform Generation

```
Implement the Terraform generation stage for the Terraform Generator Service.

Reference: docs/PDD.md (Terraform Generation Strategy)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 5)

Requirements:
1. Create terraform/template_selector.py: map resource type to template file
2. Create terraform/generator.py: render Jinja2 templates with resource data
3. Create terraform/writer.py: write .tf files to output directory
4. Create templates for: main.tf.j2, aws_s3_bucket.tf.j2, aws_instance.tf.j2, aws_security_group.tf.j2, aws_vpc.tf.j2, aws_subnet.tf.j2, aws_s3_bucket_versioning.tf.j2
5. Group resources by type (e.g., s3_buckets.tf)
6. Add unit tests in tests/unit/test_generator.py

Template variable contract: resource (or resources list), provider_config (optional)
```

### Pipeline Orchestration

```
Implement the synchronous pipeline orchestrator for the Terraform Generator Service.

Reference: docs/PDD.md (Event Flow, Architecture)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 6)

Requirements:
1. Create events/payloads.py: dataclasses for all event payloads
2. Create orchestrator that chains: ingest → parse → extract → normalize → validate → select → generate → output
3. On validation failure: emit processing.failed, stop
4. On success: write Terraform files to output/{correlation_id}/, emit processing.completed
5. Pass correlation_id through entire pipeline
6. Add integration test: MD file → Terraform files on disk

Do not integrate event broker yet. Use in-memory/synchronous flow.
```

---

## Constraints to Enforce

When implementing, **always**:

- **Do not** add Terraform execution (plan, apply, destroy)
- **Do not** support non-AWS providers in V1
- **Do not** couple the parser to Terraform generation — normalized output is template-agnostic
- **Do** use the exact event names from PDD (e.g., `architecture.ingest.requested`)
- **Do** use the exact module/package names from PDD folder structure
- **Do** limit V1 to the six AWS resource types: aws_s3_bucket, aws_s3_bucket_versioning, aws_instance, aws_security_group, aws_vpc, aws_subnet

---

## Key File References

| Concern | File(s) |
|---------|---------|
| Domain models | `src/terraform_generator/domain/models.py` |
| JSON Schema | `schemas/architecture_v1.json` |
| Event payloads | `src/terraform_generator/events/payloads.py` |
| Config | `src/terraform_generator/config.py` |
| Sample input | `tests/fixtures/sample_architectures/` |

---

## Checklist Before Submitting a Feature

- [ ] Implementation matches PDD architecture and naming
- [ ] Unit tests added/updated
- [ ] No Terraform execution code
- [ ] Domain model remains template-agnostic
- [ ] Validation errors use documented error codes
