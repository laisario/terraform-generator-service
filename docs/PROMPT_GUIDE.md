# Prompt Guide for Implementation

**Purpose:** This guide helps future Cursor prompts implement the Terraform Generator Service feature-by-feature without losing architectural consistency.

**Reference documents:** [PDD.md](./PDD.md), [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md), [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md), [DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md)

---

## How to Use This Guide

When implementing a feature, **cite the relevant PDD section** and follow the prescribed structure. Do not invent new patterns that conflict with the documented architecture.

---

## Recommended Implementation Order

1. **Foundation** — Domain models, schemas (input + domain), config (Phase 1)
2. **JSON Ingestion + Validation** — First feature (see below)
3. **Service Analysis** — Analyze recursos; map servico/config to resource list
4. **Normalization** — Domain model + dependency resolution
5. **Validation** — Domain JSON Schema + custom rules
6. **Terraform Generation** — Templates, selector, generator
7. **Pipeline** — Synchronous orchestration
8. **Artifact Storage** — Environment-based: local only (dev) or S3 only (production)
9. **Event Bus** — Optional; defer if sync API suffices

---

## Suggested First Feature to Implement

**Feature:** *JSON Ingestion + Input Validation*

**Prompt template:**

```
Implement the JSON ingestion and input validation stage for the Terraform Generator Service.

Reference: docs/PDD.md (Architecture, JSON Input Contract)
Reference: docs/IMPLEMENTATION_ROADMAP.md (Suggested First Feature)

Requirements:
1. Create ingestion/loader.py: load JSON from file path or string
2. Create input/validator.py: validate against schemas/input_v1.json
3. Reject malformed structure (missing analise_entrada, invalid recursos)
4. Return clear validation errors with path/field info
5. Add unit tests in tests/unit/test_ingestion.py and test_input_validation.py

Acceptance criteria:
- Loader.load_from_path("path/to/input.json") returns parsed JSON dict
- InputValidator.validate(data) returns validated payload when structure is correct
- Invalid JSON raises validation error with clear message

Sample input: See tests/fixtures/sample_inputs/web_app.json
```

---

## Feature-Specific Prompt Templates

### Service Analysis

```
Implement the service analysis stage for the Terraform Generator Service.

Reference: docs/PDD.md (Service Analysis, JSON Input Contract)
Reference: docs/DEVELOPMENT_CHECKLIST.md (Phase 3)

Requirements:
1. Create input/analyzer.py: analyze vibe_economica.recursos and vibe_performance.recursos
2. Interpret servico to map to Terraform resource type
3. Interpret config (string or object) into resource attributes
4. Produce analyzed resource list for normalization
5. Add unit tests in tests/unit/test_service_analysis.py

V1 focus: Map servico to V1 allowed types; reject unsupported services.
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
2. Create orchestrator that chains: ingest → JSON validate → service analysis → normalize → validate → select → generate → output
3. On validation failure: emit processing.failed, stop
4. On success: persist Terraform files (local or S3 per ENVIRONMENT), emit processing.completed
5. Pass correlation_id through entire pipeline
6. Add integration test: JSON file → Terraform files on disk

Do not integrate event broker yet. Use in-memory/synchronous flow.
```

### Artifact Storage (Environment-Based Persistence)

```
Implement the artifact storage for the Terraform Generator Service.

Reference: docs/ARTIFACT_STORAGE.md (full specification)
Reference: docs/PDD.md (Artifact Storage, Event Flow)

Requirements:
1. Add ENVIRONMENT to config (from .env); default dev if unset
2. Create storage handler that branches on ENVIRONMENT:
   - dev: write to outputs/{job_id}/; no upload
   - production: write locally, then upload all files to Cloudflare
3. Production upload: use boto3 with S3_API from .env; bucket vibe-cloud, prefix outputs/
4. Object key format: outputs/{job_id}/{file_name}
5. Upload occurs ONLY when ENVIRONMENT=production, AFTER successful local write
6. On upload failure: emit architecture.artifacts.upload.failed with partial_uploads; job marked failed
7. Add logging: storage strategy, upload start, per-file success, completion, failure
8. Add unit tests: dev path (no upload), production path (mock S3)

Do NOT change bucket name (vibe-cloud) or prefix (outputs/).
```

---

## Constraints to Enforce

When implementing, **always**:

- **Do not** add Terraform execution (plan, apply, destroy)
- **Do not** support non-AWS providers in V1
- **Do not** couple input handling to Terraform generation — normalized output is template-agnostic
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
| Sample input | `tests/fixtures/sample_inputs/` |
| Artifact storage | `docs/ARTIFACT_STORAGE.md` |

---

## Checklist Before Submitting a Feature

- [ ] Implementation matches PDD architecture and naming
- [ ] Unit tests added/updated
- [ ] No Terraform execution code
- [ ] Domain model remains template-agnostic
- [ ] Validation errors use documented error codes
