# Test Specifications — Terraform Generator Service

**Input contract:** JSON (not Markdown). See `schemas/input_v1.json` and `docs/PDD.md`.

---

## Test Coverage Requirements

### Valid JSON Input

| Test Case | Fixture | Expected |
|-----------|---------|----------|
| Valid JSON with `analise_entrada` | `web_app.json` | Pipeline succeeds; Terraform files generated |
| Valid JSON with `vibe_economica` only | `vibe_economica_only.json` | Resources from vibe_economica used; generation succeeds |
| Valid JSON with `vibe_performance` only | `vibe_performance_only.json` | Resources from vibe_performance used; generation succeeds |
| Valid JSON with both vibes | `web_app.json` | Pipeline determines which vibe(s) to use; generation succeeds |
| Multiple recursos in one vibe | `multi_recursos.json` | All resources normalized and generated |

### Invalid JSON Input

| Test Case | Fixture | Expected |
|-----------|---------|----------|
| Missing `analise_entrada` | `invalid_missing_analise.json` | Validation error; pipeline fails before generation |
| Malformed JSON structure | (invalid JSON) | Clear validation error with path/field info |
| Unsupported service in recursos | `invalid_unsupported_service.json` | Validation error (e.g., `resource_type_unsupported`); pipeline fails |
| Malformed config values | (config does not match expected for servico) | Validation error; pipeline fails |

### Normalization & Generation

| Test Case | Expected |
|-----------|----------|
| Successful normalization | Analyzed resources → valid `Architecture` domain model |
| Successful generation | Domain model → correct `.tf` files (main.tf, s3_buckets.tf, instances.tf, etc.) |

---

## Fixture Reference

| Fixture | Purpose |
|---------|---------|
| `web_app.json` | Full example: analise_entrada + vibe_economica + vibe_performance |
| `vibe_economica_only.json` | Only vibe_economica |
| `vibe_performance_only.json` | Only vibe_performance |
| `multi_recursos.json` | Multiple resources (S3, security group, instance) |
| `invalid_missing_analise.json` | Missing required analise_entrada |
| `invalid_unsupported_service.json` | Contains aws_lambda_function (not in V1) |

---

## Integration Test: Pipeline

**Test:** `tests/integration/test_pipeline.py::test_pipeline_web_app`

**Spec:**
- Input: `tests/fixtures/sample_inputs/web_app.json`
- Expected: `ProcessingCompletedPayload` with `output_path` pointing to generated Terraform directory
- Assert: `main.tf`, `s3_buckets.tf`, `security_groups.tf`, `instances.tf` exist
- Environment: `dev` (local persistence)

**Note:** This test will fail until the code is migrated from Markdown to JSON. The fixture path and assertions describe the target behavior.
