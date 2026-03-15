# Test Specifications — Terraform Generator Service

**Input contract:** Root must be a non-empty JSON array. Each item must contain an `output` object with `analise_entrada` and optional `vibe_economica`/`vibe_performance`. See `schemas/input_v1.json` and `docs/PDD.md`.

---

## Test Coverage Requirements

### Valid JSON Input

| Test Case | Fixture | Expected |
|-----------|---------|----------|
| Valid array with `analise_entrada` in output | `web_app.json` | Pipeline succeeds; Terraform files generated |
| Valid array with `vibe_economica` only | `vibe_economica_only.json` | Resources from vibe_economica used; generation succeeds |
| Valid array with `vibe_performance` only | `vibe_performance_only.json` | Resources from vibe_performance used; generation succeeds |
| Valid array with both vibes | `web_app.json` | Pipeline merges vibes; generation succeeds |
| Multiple recursos in one vibe | `multi_recursos.json` | All resources normalized and generated |
| Valid array with multiple items | `valid_multiple_items.json` | First item's output is processed |

### Invalid JSON Input

| Test Case | Fixture | Expected |
|-----------|---------|----------|
| Empty array | `invalid_empty_array.json` | Validation error; pipeline fails |
| Item without `output` | `invalid_item_without_output.json` | Validation error; pipeline fails |
| `output` not an object | `invalid_output_not_object.json` | Validation error; pipeline fails |
| Missing `analise_entrada` in output | `invalid_missing_analise.json` | Validation error; pipeline fails before generation |
| Object at root (old format) | (plain object) | Ingestion error: root must be array |
| Unsupported service in recursos | `invalid_unsupported_service.json` | Validation error; pipeline fails |

### Normalization & Generation

| Test Case | Expected |
|-----------|----------|
| Successful normalization | Analyzed resources → valid `Architecture` domain model |
| Successful generation | Domain model → correct `.tf` files (main.tf, s3_buckets.tf, instances.tf, etc.) |

---

## Fixture Reference

| Fixture | Purpose |
|---------|---------|
| `web_app.json` | Full example: array with output containing analise_entrada + vibe_economica + vibe_performance |
| `vibe_economica_only.json` | Array with output containing only vibe_economica |
| `vibe_performance_only.json` | Array with output containing only vibe_performance |
| `multi_recursos.json` | Multiple resources (S3, security group, instance) |
| `valid_multiple_items.json` | Array with multiple items (first is processed) |
| `invalid_empty_array.json` | Empty array (rejected) |
| `invalid_item_without_output.json` | Item missing `output` field |
| `invalid_output_not_object.json` | Item where `output` is not an object |
| `invalid_missing_analise.json` | Output missing required analise_entrada |
| `invalid_unsupported_service.json` | Contains aws_lambda_function (not in V1) |

---

## Integration Test: Pipeline

**Test:** `tests/integration/test_pipeline.py::test_pipeline_web_app`

**Spec:**
- Input: `tests/fixtures/sample_inputs/web_app.json` (array format)
- Expected: `ProcessingCompletedPayload` with `output_path` pointing to generated Terraform directory
- Assert: `main.tf`, `s3_buckets.tf`, `security_groups.tf`, `instances.tf` exist
- Environment: `dev` (local persistence)
