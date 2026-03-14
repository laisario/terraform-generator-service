# Artifact Storage — Environment-Based Persistence

**Feature:** Persist generated Terraform artifacts; behavior depends on environment (dev vs production)  
**Status:** Documented — Ready for implementation  
**Reference:** [PDD.md](./PDD.md)

---

## Overview

Generated Terraform artifacts are produced as a **directory of multiple files per job**. The persistence strategy depends on the `ENVIRONMENT` variable:

- **Development (`ENVIRONMENT=dev`):** Artifacts are saved **locally on disk** only. No upload to cloud storage.
- **Production (`ENVIRONMENT=production`):** Artifacts are written locally, then **uploaded to Cloudflare object storage** via the S3-compatible API.

This allows developers to inspect generated files during development without requiring cloud storage, while production ensures durable, accessible storage.

---

## Directory Structure for Generated Outputs

### Per-Job Directory

Each generation job produces a **unique directory** containing multiple Terraform files. The directory name **must** be the `job_id` (correlation_id).

**All files in the directory must be persisted** according to the environment-based strategy (see below).

**Generated output structure:**

```
outputs/{job_id}/
├── main.tf
├── variables.tf
├── outputs.tf
├── s3_buckets.tf
├── instances.tf
├── security_groups.tf
├── vpcs.tf
├── subnets.tf
└── ...
```

**Example:**

```
outputs/5421c596-869b-410a-8f40-9d386256d985/
├── main.tf
├── s3_buckets.tf
├── instances.tf
├── security_groups.tf
├── vpcs.tf
└── subnets.tf
```

### Key Points

- **One directory per job:** Each generation job produces exactly one output directory.
- **Job ID as directory name:** The `job_id` (correlation_id) is used as the directory name.
- **Multiple files per job:** All generated `.tf` files are placed inside that directory.
- **All files must be persisted:** Every file in the directory must be stored (locally in dev, or uploaded in production).

---

## Environment-Based Storage Behavior

The `ENVIRONMENT` variable (from `.env`) determines where artifacts are persisted.

| Variable | Value | Behavior |
|----------|-------|----------|
| `ENVIRONMENT` | `dev` | **Local storage only.** Artifacts are saved to a local directory. No upload to object storage. |
| `ENVIRONMENT` | `production` | **Local write + cloud upload.** Artifacts are written locally, then uploaded to Cloudflare object storage. |

### Generation Pipeline

1. Terraform artifacts are generated.
2. Artifacts are placed in a local directory structure: `outputs/{job_id}/{file_name}`.
3. The storage handler decides the destination based on `ENVIRONMENT`:

| ENVIRONMENT | Action |
|-------------|--------|
| `dev` | Artifacts remain stored locally. No upload. |
| `production` | Artifacts are uploaded to S3-compatible storage (Cloudflare). |

### Development Environment (`ENVIRONMENT=dev`)

- **Purpose:** Allow developers to inspect generated Terraform files during development without requiring cloud storage.
- **Behavior:** Files are written to a local directory. **No upload** to object storage.
- **Local path example:** `outputs/5421c596-869b-410a-8f40-9d386256d985/main.tf` (or configurable base path + `{job_id}/{file_name}`)

### Production Environment (`ENVIRONMENT=production`)

- **Purpose:** Durable, accessible storage for generated artifacts.
- **Behavior:** Files are written locally first, then **all files uploaded** to Cloudflare object storage via S3-compatible API.
- **Configuration:** Uses existing S3-compatible credentials and endpoint from `.env`.

---

## Object Storage Configuration (Production Only)

### Bucket and Prefix

| Setting | Value | Notes |
|---------|-------|-------|
| **Bucket** | `vibe-cloud` | Fixed; do not change |
| **Prefix** | `outputs/` | Fixed; do not change |
| **Object key format** | `outputs/{job_id}/{file_name}` | See below |

### Object Key Naming Strategy

| Component | Description | Example |
|-----------|-------------|---------|
| Prefix | Fixed prefix | `outputs/` |
| Job ID | Correlation ID (UUID) | `5421c596-869b-410a-8f40-9d386256d985` |
| File name | Terraform file name | `main.tf` |

**Full object key pattern:**

```
outputs/{job_id}/{file_name}
```

**Examples:**

| Local path | Object key (production) |
|------------|-------------------------|
| `outputs/5421c596-869b-410a-8f40-9d386256d985/main.tf` | `outputs/5421c596-869b-410a-8f40-9d386256d985/main.tf` |
| `outputs/5421c596-869b-410a-8f40-9d386256d985/s3_buckets.tf` | `outputs/5421c596-869b-410a-8f40-9d386256d985/s3_buckets.tf` |
| `outputs/5421c596-869b-410a-8f40-9d386256d985/variables.tf` | `outputs/5421c596-869b-410a-8f40-9d386256d985/variables.tf` |

---

## S3-Compatible API Configuration (Production)

### Credentials and Endpoint

Storage uses the **S3-compatible API credentials and endpoint** configured in `.env`.

**Expected environment variables (example):**

- `S3_API` — Endpoint URL (e.g., Cloudflare R2 endpoint)
- `AWS_ACCESS_KEY_ID` (or equivalent) — Access key for S3-compatible API
- `AWS_SECRET_ACCESS_KEY` (or equivalent) — Secret key for S3-compatible API
- `AWS_REGION` (or equivalent) — Region, if required by the provider

**Implementation note:** The implementation must be generic for S3-compatible storage (e.g., AWS S3, Cloudflare R2, MinIO). Use standard S3 client libraries (e.g., `boto3`) with configurable endpoint and credentials.

---

## Architecture Impact

### Stage 8: Output — Extended Responsibility

The Output stage (Stage 8) is extended to:

1. **Write to local disk** — Generate Terraform files into `outputs/{job_id}/` (or configurable base path)
2. **Storage handler** — Based on `ENVIRONMENT`:
   - **dev:** Stop after local write. No further action.
   - **production:** Upload all files in that directory to Cloudflare object storage.

### New Component: Artifact Storage Handler

| Component | Responsibility |
|-----------|----------------|
| **Artifact Storage Handler** | Persist artifacts based on `ENVIRONMENT`: local only (dev) or local + upload (production) |
| **Artifact Uploader** | (Production only) Upload all files in a job output directory to object storage using S3-compatible API |

### Placement in Pipeline

```
[Generation] ──► [Local Write] ──► [Storage Handler]
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                         │
              ENVIRONMENT=dev                          ENVIRONMENT=production
                    │                                         │
                    ▼                                         ▼
            [Output Complete]                    [Artifact Upload] ──► [Output Complete]
            (local only)                         (or [Upload Failed])
```

Upload occurs **only in production** and **after** successful local artifact generation. If generation fails, no upload is attempted.

---

## Artifact Storage Strategy

### Local Storage Strategy (All Environments)

- **When:** Immediately after Terraform files are generated.
- **Where:** Local directory `outputs/{job_id}/` (or configurable base path).
- **What:** All generated `.tf` files.
- **Directory name:** Must be the `job_id`.

### Upload Strategy (Production Only)

- **When:** Immediately after Terraform files are successfully written to the local output directory.
- **Condition:** Only if `ENVIRONMENT=production` and generation completed without errors.
- **Scope:** All files in `outputs/{job_id}/`
- **How:** Iterate over each file; upload with object key `outputs/{job_id}/{file_name}` to bucket `vibe-cloud`.

### Idempotency

- Re-uploading the same job_id overwrites existing objects.
- Partial uploads from a previous run may leave orphaned objects; see Failure Handling.

---

## Output Lifecycle

| Phase | Description |
|-------|-------------|
| **1. Generation** | Terraform files generated in memory |
| **2. Local write** | Files written to `outputs/{job_id}/` |
| **3. Storage decision** | Storage handler checks `ENVIRONMENT` |
| **4a. Dev** | No further action. Job complete. |
| **4b. Production** | Each file uploaded to `outputs/{job_id}/{file_name}` in bucket `vibe-cloud` |
| **5. Completion** | Job marked complete; `architecture.processing.completed` emitted |

### Retention

- Local output directory may be retained or cleaned up per configuration.
- Object storage retention (production) is managed by Cloudflare/bucket policy; not in scope for this service.

---

## Event Pipeline Impact

### Existing Events

| Event | Change |
|-------|--------|
| `architecture.terraform.generated` | Payload includes `terraform_files` list; used as input for storage |
| `architecture.processing.completed` | Emitted after local write (dev) or after successful upload (production). Payload may include `storage_uris` or `object_keys` in production. |

### Suggested New Event (Optional, Production Only)

| Event Name | Trigger | Payload |
|------------|---------|---------|
| `architecture.artifacts.uploaded` | All files uploaded successfully (production) | `{ "correlation_id", "job_id", "object_keys": ["outputs/{job_id}/main.tf", ...], "bucket": "vibe-cloud" }` |

### Failure Event (Production Only)

| Event Name | Trigger | Payload |
|------------|---------|---------|
| `architecture.artifacts.upload.failed` | Upload fails (any file) in production | `{ "correlation_id", "job_id", "stage": "artifact_upload", "error": "...", "partial_uploads": [...] }` |

---

## Error Handling for Uploads (Production Only)

Upload failures apply only when `ENVIRONMENT=production`.

### Expected Behavior on Upload Failure

- **Error must be logged:** Log the error with `job_id` and `correlation_id`.
- **Job status:** Job should be marked as **failed** or **partially completed**.
- **Partial uploads must be detectable:** Log and include in failure payload the list of object keys that were successfully uploaded before the failure.

### Partial Uploads

If upload fails **after** some files have been uploaded:

- **Partial uploads must be detectable:** Log the list of successfully uploaded object keys before failure.
- **Payload:** Include `partial_uploads` in the failure event (list of object keys that were uploaded).
- **Recovery:** A future implementation may support retry or cleanup of partial uploads.

### Upload Failure Behavior

| Scenario | Behavior |
|----------|----------|
| **All uploads succeed** | Emit `architecture.processing.completed` (or `architecture.artifacts.uploaded`) |
| **First file fails** | Emit `architecture.artifacts.upload.failed`; no partial uploads; job marked failed |
| **Nth file fails** | Emit `architecture.artifacts.upload.failed`; include `partial_uploads` with keys of files 1..N-1; job marked failed or partially completed |

### Job Status

- On upload failure, the job should be considered **failed** (or **partially completed** if some files were uploaded).
- Failure must be visible in logs and, if applicable, job status.

---

## Logging and Observability

### Required Log Events

| Event | When | Data | Environment |
|-------|------|------|-------------|
| **Local write completed** | After files written to disk | `job_id`, `path`, `file_count` | All |
| **Storage strategy** | When storage handler runs | `job_id`, `ENVIRONMENT` | All |
| **Upload skipped** | When ENVIRONMENT=dev | `job_id`, reason | dev |
| **Upload started** | Before first file upload | `job_id`, `file_count` | production |
| **File uploaded** | After each successful upload | `job_id`, `object_key` | production |
| **Upload completed** | All files uploaded | `job_id`, `object_keys[]` | production |
| **Upload failed** | Any upload failure | `job_id`, `error`, `partial_uploads[]` | production |

### Correlation ID

- Use `correlation_id` (job_id) in all log messages for traceability.
- Include `correlation_id` in failure events for downstream consumers.

### Detectability of Partial Uploads

- Log each successful upload as it completes (production only).
- On failure, log the full list of object keys that were uploaded before the failure.
- This allows operators or tooling to identify and optionally clean up partial uploads.

---

## Implementation Checklist

- [ ] Add `ENVIRONMENT` to config (from `.env`); default `dev` if unset
- [ ] Implement storage handler that branches on `ENVIRONMENT`
- [ ] **Dev:** Write to local `outputs/{job_id}/`; no upload
- [ ] **Production:** Add S3-compatible client (e.g., `boto3`); upload after local write
- [ ] Add config for bucket (`vibe-cloud`), prefix (`outputs/`), and credentials from `.env`
- [ ] Implement `ArtifactUploader` that uploads a directory of files (production only)
- [ ] Emit `architecture.artifacts.upload.failed` on upload failure with `partial_uploads`
- [ ] Add logging for storage strategy, upload start, per-file success, completion, failure
- [ ] Add unit tests for storage handler (dev path, production path with mock S3)
- [ ] Add integration test with local or test bucket (optional)

---

## Configuration Reference

| Config Key | Value | Source | Notes |
|------------|-------|--------|-------|
| `ENVIRONMENT` | `dev` or `production` | `.env` | Determines storage strategy |
| `TFGEN_STORAGE_BUCKET` | `vibe-cloud` | Env (default) | Production only |
| `TFGEN_STORAGE_PREFIX` | `outputs/` | Env (default) | Production only |
| `S3_API` | Endpoint URL | `.env` | Production only |
| `AWS_ACCESS_KEY_ID` | Access key | `.env` | Production only |
| `AWS_SECRET_ACCESS_KEY` | Secret key | `.env` | Production only |

---

## Summary

- **Output:** Directory per job (`outputs/{job_id}/`) with multiple `.tf` files. All files must be persisted.
- **Environment-based:** `ENVIRONMENT=dev` → local only; `ENVIRONMENT=production` → local + upload to Cloudflare.
- **Local storage:** Files written to `outputs/{job_id}/{file_name}` in all environments.
- **Cloud upload (production):** All files uploaded to `outputs/{job_id}/{file_name}` in bucket `vibe-cloud`.
- **Storage:** S3-compatible API; credentials from `.env`. Used only when `ENVIRONMENT=production`.
- **Failure (production):** Log error; emit failure event; include partial uploads for detectability; job marked failed.
