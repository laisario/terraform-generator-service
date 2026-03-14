# Development Checklist

**Service:** Terraform Generator Service  
**Reference:** [PDD.md](./PDD.md) | [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)

Use this checklist to track implementation progress. Check off items as they are completed.

---

## Phase 1: Foundation

### Project Setup
- [ ] Create `pyproject.toml` with dependencies (Python 3.11+, pytest, ruff, pydantic, jinja2, jsonschema)
- [ ] Create `requirements.txt` or use uv/poetry for dependency management
- [ ] Set up `src/terraform_generator` package structure
- [ ] Configure ruff (or black + isort) for linting/formatting
- [ ] Add pre-commit hooks (optional)
- [ ] Create `scripts/run_worker.py` entry point

### Domain Models
- [ ] Define `Architecture` model (id, name, provider, resources, metadata)
- [ ] Define `InfrastructureResource` model (type, logical_name, attributes, dependencies)
- [ ] Define `ArchitectureMetadata` model (source_file, parsed_at, version)
- [ ] Define domain exceptions in `domain/exceptions.py`

### JSON Schemas
- [ ] Create `schemas/input_v1.json` (input contract: analise_entrada, vibes, recursos)
- [ ] Create `schemas/architecture_v1.json`
- [ ] Include all V1 resource types in enum: aws_s3_bucket, aws_s3_bucket_versioning, aws_instance, aws_security_group, aws_vpc, aws_subnet
- [ ] Add `$defs` for InfrastructureResource and ArchitectureMetadata
- [ ] Add `logical_name` pattern: `^[a-z][a-z0-9_]*$`

### Configuration
- [ ] Implement `config.py` with Pydantic Settings
- [ ] Support configurable output directory
- [ ] Support configurable event broker (when applicable)

---

## Phase 2: JSON Ingestion & Validation

### Ingestion
- [ ] Implement `ingestion/loader.py` — load JSON from file path
- [ ] Implement content-based loading (string in, parsed dict out)
- [ ] Handle file-not-found errors with clear messages
- [ ] Handle encoding errors (UTF-8) and JSON parse errors
- [ ] Add optional file size limit (e.g., 1MB)

### JSON Validation
- [ ] Load `schemas/input_v1.json`
- [ ] Validate incoming JSON against input schema
- [ ] Reject malformed structure (missing `analise_entrada`, invalid `recursos`)
- [ ] Return clear validation errors with path/field info
- [ ] Unit test: valid JSON → validated payload; invalid JSON → error

---

## Phase 3: Service Analysis

### Analysis Logic
- [ ] Iterate over `vibe_economica.recursos` and `vibe_performance.recursos`
- [ ] Interpret `servico` to map to Terraform resource type
- [ ] Interpret `config` (string or object) into resource attributes
- [ ] Produce analyzed resource list for normalization
- [ ] Unit test: JSON with recursos → analyzed resource list

---

## Phase 4: Normalization & Validation

### Normalization
- [ ] Map analyzed resources to `InfrastructureResource`
- [ ] Resolve `dependencies` from references (e.g., `aws_security_group.web_sg`)
- [ ] Detect and reject circular dependencies
- [ ] Build `Architecture` root with metadata
- [ ] Unit test: raw records → valid Architecture

### Validation
- [ ] Load JSON Schema from `schemas/architecture_v1.json`
- [ ] Validate domain model (as dict) against schema
- [ ] Implement custom rules: circular deps, undefined refs, duplicate logical names
- [ ] Collect errors (blocking) and warnings (non-blocking)
- [ ] Emit validation result with error/warning lists
- [ ] Unit test: valid/invalid models → correct pass/fail

---

## Phase 5: Terraform Generation

### Templates
- [ ] Create `templates/terraform/aws/main.tf.j2` (provider block)
- [ ] Create `aws_s3_bucket.tf.j2`
- [ ] Create `aws_s3_bucket_versioning.tf.j2`
- [ ] Create `aws_instance.tf.j2`
- [ ] Create `aws_security_group.tf.j2`
- [ ] Create `aws_vpc.tf.j2`
- [ ] Create `aws_subnet.tf.j2`

### Generation Logic
- [ ] Implement `terraform/template_selector.py` — map resource type to template
- [ ] Implement `terraform/generator.py` — render Jinja2 with resource data
- [ ] Implement `terraform/writer.py` — write .tf files to output directory
- [ ] Group resources by type (e.g., all S3 buckets in `s3_buckets.tf`)
- [ ] Generate `main.tf` with AWS provider block
- [ ] Unit test: domain model → correct .tf output

---

## Phase 6: Event Pipeline

### Event Payloads
- [ ] Define `events/payloads.py` — dataclasses for all event payloads
- [ ] `IngestRequestedPayload` (file_path, content, correlation_id)
- [ ] `InputValidatedPayload`, `ServicesAnalyzedPayload`, `NormalizedPayload`
- [ ] `ValidatedPayload` (valid, errors, warnings)
- [ ] `TemplatesSelectedPayload`, `TerraformGeneratedPayload`
- [ ] `ProcessingCompletedPayload`, `ProcessingFailedPayload`

### Synchronous Pipeline
- [ ] Implement orchestrator that chains all stages
- [ ] Ingest → JSON Validate → Service Analysis → Normalize → Validate → Select → Generate → Output
- [ ] Emit `architecture.processing.completed` on success
- [ ] Emit `architecture.processing.failed` on any stage error
- [ ] Pass `correlation_id` through entire pipeline

### Output
- [ ] Write generated Terraform files to `output/{job_id}/` (directory per job)
- [ ] Optional: publish events to stdout or log

---

## Phase 6b: Artifact Storage (Environment-Based)

Reference: [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md)

- [ ] Add `ENVIRONMENT` to config (from `.env`); default `dev`
- [ ] Implement storage handler: branch on `ENVIRONMENT`
- [ ] **Dev:** Write to `outputs/{job_id}/`; no upload
- [ ] **Production:** Add S3-compatible client (boto3), upload all files in `outputs/{job_id}/`
- [ ] Object key format: `outputs/{job_id}/{file_name}` in bucket `vibe-cloud`
- [ ] Upload only when `ENVIRONMENT=production`, after successful local write
- [ ] On failure: emit `architecture.artifacts.upload.failed` with `partial_uploads`; job marked failed
- [ ] Add logging for storage strategy, upload start, per-file, completion, failure
- [ ] Unit tests: dev path, production path with mocked S3

---

## Phase 7: Event Bus (Optional for V1)

- [ ] Choose broker: Redis Streams or RabbitMQ
- [ ] Implement `events/publisher.py`
- [ ] Implement `events/consumer.py` — consume `architecture.ingest.requested`
- [ ] Wire consumer to pipeline orchestrator
- [ ] Integration test: publish ingest event → receive completed/failed

---

## Phase 8: Testing & Polish

### Unit Tests
- [ ] `tests/unit/test_ingestion.py`
- [ ] `tests/unit/test_input_validation.py`
- [ ] `tests/unit/test_service_analysis.py`
- [ ] `tests/unit/test_normalization.py`
- [ ] `tests/unit/test_validation.py`
- [ ] `tests/unit/test_generator.py`

### Integration Tests
- [ ] `tests/integration/test_pipeline.py` — JSON file → Terraform files
- [ ] Sample fixtures: `tests/fixtures/sample_inputs/*.json`

### Documentation
- [ ] README with quick start
- [ ] Sample architecture file in docs or fixtures
- [ ] Usage examples (CLI or API)

---

## Definition of Done (V1)

- [ ] End-to-end: JSON file in → Terraform files out
- [ ] All six V1 AWS resource types supported
- [ ] JSON Schema validation passes for valid input
- [ ] Validation errors block pipeline with clear messages
- [ ] No Terraform execution (files only)

---

## Quick Reference: V1 AWS Resource Types

| Type | Template |
|------|----------|
| aws_s3_bucket | aws_s3_bucket.tf.j2 |
| aws_s3_bucket_versioning | aws_s3_bucket_versioning.tf.j2 |
| aws_instance | aws_instance.tf.j2 |
| aws_security_group | aws_security_group.tf.j2 |
| aws_vpc | aws_vpc.tf.j2 |
| aws_subnet | aws_subnet.tf.j2 |
