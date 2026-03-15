# Terraform Generator Service — Prompt-Driven Development Document

**Version:** 2.0  
**Status:** Planning  
**Last Updated:** 2025-03-14

---

## Overview

The **Terraform Generator Service** is a Python event-driven backend service that receives **JSON input** describing infrastructure options (vibes), validates the structure and requested services, normalizes the content into a JSON-Schema-aligned internal representation, and generates Terraform configuration files from AWS-oriented templates.

The service does **not** execute Terraform. It produces ready-to-use `.tf` files that can be applied by external tooling (e.g., CI/CD, Terraform Cloud, or manual `terraform apply`).

### Service Purpose (One-Liner)

*Receive JSON infrastructure definitions (vibe_economica, vibe_performance) → validate structure and requested services → normalize into domain model → generate AWS Terraform files from templates.*

---

## Objective

**Primary goal:** Build a Python event-driven service that receives **JSON files** as input, validates the JSON structure and requested services, analyzes which Terraform resources should be created, applies validation rules, normalizes into the internal domain model, and generates Terraform files from AWS-oriented templates.

**Success criteria for V1:**
- JSON input files can be ingested and validated against input schema
- Requested services/resources are analyzed from `vibe_economica.recursos` and `vibe_performance.recursos`
- Validation rules determine which services are supported and configs are valid
- Normalized output validates against the internal domain schema
- Terraform files are generated from templates for supported AWS resource types
- The pipeline is event-driven with clear stage boundaries

---

## V1 Scope

| In Scope | Description |
|----------|-------------|
| JSON ingestion | Accept `.json` files as input (file path or content) |
| JSON schema validation | Validate input structure against `schemas/input_v1.json` |
| Service/resource analysis | Analyze `recursos` from vibes; interpret `servico` and `config` |
| Business validation | Validate requested services against supported types; validate configs |
| Normalization | Convert validated JSON into internal domain model |
| Domain schema validation | Validate normalized output against `schemas/architecture_v1.json` |
| Terraform template selection | Map domain model entities to template identifiers |
| Terraform file generation | Render `.tf` files from Jinja2 templates |
| Event-driven flow | Process through discrete stages with event exchange |
| AWS-first focus | Support a small, fixed set of AWS resource types |

---

## Out of Scope

| Out of Scope | Rationale |
|--------------|-----------|
| Terraform execution (`plan`, `apply`, `destroy`) | Explicitly deferred; V1 produces files only |
| Non-AWS providers (GCP, Azure) | V1 is AWS-first; multi-provider is future work |
| State management | No Terraform state handling |
| Drift detection | Requires execution |
| Interactive CLI | V1 is service/API oriented |
| Real-time streaming | Batch processing per event |
| Markdown authoring UI | Input is files; no WYSIWYG editor |
| Template marketplace | Fixed built-in templates only |

---

## Assumptions

1. **Input format:** The service receives **JSON** as a non-empty array. Each item must contain an `output` object with `analise_entrada` and optionally `vibe_economica` and/or `vibe_performance`, each with `recursos` listing requested services and configs.
2. **AWS focus:** All V1 resources map to AWS provider (`hashicorp/aws`); no multi-provider logic.
3. **Event broker:** An event bus (e.g., Redis Streams, RabbitMQ, or SQS) is available; exact choice is configurable.
4. **Python version:** Python 3.11+ for type hints and modern syntax.
5. **Terraform version:** Generated output targets Terraform 1.x and AWS provider 5.x.
6. **Single-tenant processing:** Each event represents one architecture file; no batching of multiple files per event.
7. **Idempotency:** Re-processing the same input yields the same output (deterministic).
8. **No secrets in JSON:** Sensitive values (e.g., API keys) are not embedded in input JSON; they are injected at apply time.

---

## Architecture

### High-Level Stages

The system is organized into seven conceptual stages, each with clear inputs and outputs:

```
┌─────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│  1. Ingestion   │→│  2. JSON Validation     │→│  3. Service Analysis    │
│  (JSON in)      │ │  (Schema + structure)   │ │  (Requested resources)   │
└─────────────────┘ └───────────────────────┘ └───────────┬─────────────┘
                                                           │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────▼─────────────┐
│  7. Output      │←│  6. Generation  │←│  4. Normalization              │
│  (Events/files) │ │  (Terraform)    │ │  (Domain model)                │
└─────────────────┘ └─────────────────┘ └───────────┬─────────────────┘
                                                       │
                        ┌──────────────────────────────▼──────────────────────┐
                        │  5. Validation (domain rules + JSON Schema)        │
                        └───────────────────────────────────────────────────┘
```

### Stage Responsibilities

| Stage | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| **1. Ingestion** | Receive JSON (path or content), load raw JSON | Event with file path or content | Raw JSON string or parsed dict |
| **2. JSON Validation** | Validate input against `input_v1.json` schema; reject malformed structure | Raw JSON | Validated input payload |
| **3. Service Analysis** | Analyze `vibe_economica.recursos` and `vibe_performance.recursos`; interpret `servico` and `config`; determine which Terraform resources to generate | Validated input | Analyzed resource list |
| **4. Normalization** | Map analyzed resources to domain model, resolve references | Analyzed resources | Normalized domain model |
| **5. Validation** | Validate domain model against `architecture_v1.json`; apply business rules (supported types, required attributes, etc.) | Domain model (as dict) | Validation result |
| **6. Generation** | Template selection + render Terraform from templates | Domain model | Terraform file content |
| **7. Output** | Persist files (local or S3), emit events | Generated Terraform | Published events, artifacts |

### Layering

- **Ingestion / Event handling:** Adapter layer (file system, message queue)
- **JSON Validation / Service Analysis:** Application services (input handling)
- **Normalization / Validation:** Domain layer (business rules)
- **Generation:** Application services (Terraform-specific)
- **Output:** Adapter layer (file system, object storage upload, event publishing)

---

## Artifact Storage (Environment-Based Persistence)

Generated Terraform artifacts are produced as a **directory per job** containing multiple `.tf` files. Persistence depends on `ENVIRONMENT`:

- **`ENVIRONMENT=dev`:** Artifacts saved locally only. No cloud upload.
- **`ENVIRONMENT=production`:** Artifacts written locally, then uploaded to Cloudflare object storage via S3-compatible API.

**Key details:**

- **Structure:** One directory per job (`outputs/{job_id}/`) containing multiple files (e.g., `main.tf`, `s3_buckets.tf`, `instances.tf`).
- **Production upload:** Bucket `vibe-cloud`, prefix `outputs/`, object key `outputs/{job_id}/{file_name}`.
- **Configuration:** `ENVIRONMENT` from `.env`; S3-compatible credentials used only in production.

**Full specification:** See [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md) for environment-based behavior, storage strategy, output lifecycle, event pipeline, failure handling, and logging.

---

## Event Flow

### Event Naming Convention

Events use a `{domain}.{action}.{result}` pattern:

| Event Name | Trigger | Payload |
|------------|---------|---------|
| `architecture.ingest.requested` | External request to process a file | `{ "file_path": "...", "content": "...", "correlation_id": "..." }` |
| `architecture.input.validated` | JSON structure validated | `{ "correlation_id", "input_payload": {...} }` |
| `architecture.services.analyzed` | Service analysis complete | `{ "correlation_id", "analyzed_resources": [...] }` |
| `architecture.normalized` | Normalization complete | `{ "correlation_id", "domain_model": {...} }` |
| `architecture.validated` | Validation complete | `{ "correlation_id", "valid": bool, "errors": [], "warnings": [] }` |
| `architecture.templates.selected` | Template selection complete | `{ "correlation_id", "template_mappings": [...] }` |
| `architecture.terraform.generated` | Generation complete | `{ "correlation_id", "terraform_files": [{ "path": "...", "content": "..." }] }` |
| `architecture.processing.completed` | Full pipeline success (incl. artifact upload) | `{ "correlation_id", "output_path": "...", "summary": {...} }` |
| `architecture.processing.failed` | Pipeline failure | `{ "correlation_id", "stage": "...", "error": "..." }` |
| `architecture.artifacts.upload.failed` | Artifact upload failure | `{ "correlation_id", "stage": "artifact_upload", "error": "...", "partial_uploads": [...] }` |

### Correlation ID

Every event in a pipeline shares the same `correlation_id` to enable tracing and debugging.

### Event Flow Diagram

```
architecture.ingest.requested
        │
        ▼
   [Ingestion] ──► architecture.input.validated
        │
        ▼
   [JSON Validation] ──► architecture.services.analyzed
        │
        ▼
   [Service Analysis] ──► architecture.normalized
        │
        ▼
   [Normalization] ──► architecture.validated
        │
        ▼
   [Validation] ──► architecture.terraform.generated
        │
        ▼
   [Generation] ──► architecture.processing.completed
        │
        ▼
   [Output]
```

On validation failure: emit `architecture.processing.failed` and stop.  
On any other stage failure: emit `architecture.processing.failed` with `stage` and `error`.

---

## Domain Model

### Core Entities

The domain model is **provider-aware** but **template-agnostic**. It describes *what* infrastructure is needed, not *how* it is rendered.

#### 1. `Architecture`

Root container for a single architecture definition.

```python
# Conceptual structure (not code)
Architecture:
  - id: str (correlation_id)
  - name: str (from document or default)
  - provider: "aws"  # V1 only
  - resources: List[InfrastructureResource]
  - metadata: ArchitectureMetadata
```

#### 2. `InfrastructureResource`

A single infrastructure component (e.g., S3 bucket, EC2 instance).

```python
InfrastructureResource:
  - type: str          # e.g., "aws_s3_bucket", "aws_instance"
  - logical_name: str  # Terraform resource name (e.g., "main_bucket")
  - attributes: Dict[str, Any]  # Provider-specific attributes
  - dependencies: List[str]  # logical_name of dependencies
```

#### 3. `ArchitectureMetadata`

Document-level metadata.

```python
ArchitectureMetadata:
  - source_file: Optional[str]
  - parsed_at: datetime (ISO 8601)
  - version: str  # e.g., "1.0"
```

### V1 Supported AWS Resource Types

| Terraform Type | Logical Use Case | Key Attributes (examples) |
|----------------|------------------|---------------------------|
| `aws_s3_bucket` | Object storage | `bucket`, `tags` |
| `aws_s3_bucket_versioning` | S3 versioning | `bucket` (ref), `versioning_configuration` |
| `aws_instance` | Compute (EC2) | `ami`, `instance_type`, `tags` |
| `aws_security_group` | Network security | `name`, `description`, `ingress`, `egress` |
| `aws_vpc` | Network | `cidr_block`, `tags` |
| `aws_subnet` | Subnet | `vpc_id`, `cidr_block`, `availability_zone` |

V1 supports **exactly these six** resource types. Others are rejected with a validation error.

### Example Normalized Output (JSON)

```json
{
  "id": "req-abc-123",
  "name": "web-app-architecture",
  "provider": "aws",
  "metadata": {
    "source_file": "architectures/web-app.json",
    "parsed_at": "2025-03-14T10:00:00Z",
    "version": "1.0"
  },
  "resources": [
    {
      "type": "aws_s3_bucket",
      "logical_name": "assets_bucket",
      "attributes": {
        "bucket": "my-app-assets",
        "tags": {
          "Environment": "production",
          "Project": "web-app"
        }
      },
      "dependencies": []
    },
    {
      "type": "aws_instance",
      "logical_name": "web_server",
      "attributes": {
        "ami": "ami-0c55b159cbfafe1f0",
        "instance_type": "t3.micro",
        "tags": {
          "Role": "web"
        }
      },
      "dependencies": ["web_sg"]
    },
    {
      "type": "aws_security_group",
      "logical_name": "web_sg",
      "attributes": {
        "name": "web-sg",
        "description": "Security group for web servers",
        "ingress": [
          {
            "from_port": 80,
            "to_port": 80,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"]
          }
        ]
      },
      "dependencies": []
    }
  ]
}
```

---

## JSON Schema Strategy

### Schema Locations

- **Input schema:** `schemas/input_v1.json` — Validates incoming JSON structure (`analise_entrada`, `vibe_economica`, `vibe_performance`, `recursos`).
- **Domain schema:** `schemas/architecture_v1.json`
- Versioned: `architecture_v1` implies future `architecture_v2` for breaking changes

### Validation Rules

#### Errors (Blocking — Pipeline Stops)

| Code | Description | Example |
|------|-------------|---------|
| `resource_type_unsupported` | Resource type not in V1 allowed list | `aws_lambda_function` used |
| `missing_required_attribute` | Required attribute for resource type is missing | `aws_s3_bucket` without `bucket` |
| `invalid_attribute_value` | Attribute value fails type/format check | `logical_name` contains uppercase |
| `circular_dependency` | Dependency graph contains a cycle | A → B → C → A |
| `undefined_dependency` | Referenced `logical_name` does not exist | Depends on `missing_sg` |
| `duplicate_logical_name` | Two resources share the same `logical_name` | Two `main_bucket` resources |
| `invalid_schema` | Fails JSON Schema structural validation | Missing `provider` field |

#### Warnings (Non-Blocking — Logged, Pipeline Continues)

| Code | Description | Example |
|------|-------------|---------|
| `empty_resources` | No resources defined | Architecture has zero resources |
| `deprecated_attribute` | Attribute is deprecated (future use) | Reserved for future versions |
| `unused_dependency` | Declared dependency not used in attributes | Informational only |

### Error vs Warning

- **Error:** Pipeline stops; no Terraform generated; `architecture.processing.failed` emitted.
- **Warning:** Logged and included in `architecture.validated` payload; pipeline continues.

### Schema Structure (Conceptual)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/architecture_v1.json",
  "title": "Architecture",
  "type": "object",
  "required": ["id", "provider", "resources"],
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "provider": { "enum": ["aws"] },
    "metadata": { "$ref": "#/$defs/ArchitectureMetadata" },
    "resources": {
      "type": "array",
      "items": { "$ref": "#/$defs/InfrastructureResource" }
    }
  },
  "$defs": {
    "InfrastructureResource": {
      "type": "object",
      "required": ["type", "logical_name", "attributes"],
      "properties": {
        "type": { "enum": ["aws_s3_bucket", "aws_instance", "aws_security_group", "aws_vpc", "aws_subnet", "aws_s3_bucket_versioning"] },
        "logical_name": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
        "attributes": { "type": "object" },
        "dependencies": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

---

## Terraform Generation Strategy

### Template Engine

- **Engine:** Jinja2
- **Template location:** `templates/terraform/aws/`
- **Naming:** `{resource_type}.tf.j2` (e.g., `aws_s3_bucket.tf.j2`)

### Template Selection Mapping

| Domain `type` | Template File |
|---------------|---------------|
| `aws_s3_bucket` | `aws_s3_bucket.tf.j2` |
| `aws_s3_bucket_versioning` | `aws_s3_bucket_versioning.tf.j2` |
| `aws_instance` | `aws_instance.tf.j2` |
| `aws_security_group` | `aws_security_group.tf.j2` |
| `aws_vpc` | `aws_vpc.tf.j2` |
| `aws_subnet` | `aws_subnet.tf.j2` |

### Output Structure

Generated files are placed in an output directory (configurable) **per job**:

```
output/{job_id}/
├── main.tf           # Provider + backend (optional)
├── variables.tf      # Input variables (if any)
├── outputs.tf        # Output values (if any)
├── s3_buckets.tf     # One file per resource type group
├── instances.tf
├── security_groups.tf
├── vpcs.tf
├── subnets.tf
└── ...
```

**Directory-based model:** Each generation job produces a unique directory. In dev, files stay local; in production, all files are uploaded to object storage (see [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md)).

**Recommended for V1:** One `.tf` file per *resource type* (e.g., all S3 buckets in `s3_buckets.tf`) to reduce file count and match common Terraform layouts.

### Template Variable Contract

Each template receives:

- `resource`: The single `InfrastructureResource` (or list of resources of that type)
- `provider_config`: Optional provider-level config (region, etc.)

### Example Template: `aws_s3_bucket.tf.j2`

```jinja2
{% for resource in resources %}
resource "aws_s3_bucket" "{{ resource.logical_name }}" {
  bucket = "{{ resource.attributes.bucket }}"
  {% if resource.attributes.tags %}
  tags = {
    {% for k, v in resource.attributes.tags.items() %}
    "{{ k }}" = "{{ v }}"
    {% endfor %}
  }
  {% endif %}
}
{% endfor %}
```

### Generated Terraform Files (V1 Example)

For the normalized example above, expected output:

- `s3_buckets.tf` — `aws_s3_bucket.assets_bucket`
- `instances.tf` — `aws_instance.web_server`
- `security_groups.tf` — `aws_security_group.web_sg`
- `main.tf` — Provider block (`aws`), no backend in V1

---

## Suggested Python Stack

| Concern | Technology | Rationale |
|---------|------------|-----------|
| Runtime | Python 3.11+ | Type hints, performance |
| Event bus | Redis Streams or RabbitMQ | Lightweight, widely used |
| Markdown parsing | `markdown-it-py` or `mistune` | Structured AST, extensible |
| JSON Schema | `jsonschema` | Standard library |
| Templating | Jinja2 | De facto standard for Python |
| Config | Pydantic Settings | Type-safe config |
| Async | `asyncio` + `aio-pika` or `redis.asyncio` | Event-driven fits async |
| Testing | pytest, pytest-asyncio | Standard Python testing |
| Linting | ruff | Fast, opinionated |

---

## Suggested Folder Structure

```
terraform-generator-service/
├── README.md
├── pyproject.toml
├── requirements.txt
├── docs/
│   ├── PDD.md                    # This document
│   ├── IMPLEMENTATION_ROADMAP.md
│   └── DEVELOPMENT_CHECKLIST.md
├── schemas/
│   ├── input_v1.json           # Input contract (analise_entrada, vibes, recursos)
│   └── architecture_v1.json    # Domain model (normalized output)
├── templates/
│   └── terraform/
│       └── aws/
│           ├── main.tf.j2
│           ├── aws_s3_bucket.tf.j2
│           ├── aws_instance.tf.j2
│           ├── aws_security_group.tf.j2
│           ├── aws_vpc.tf.j2
│           ├── aws_subnet.tf.j2
│           └── aws_s3_bucket_versioning.tf.j2
├── src/
│   └── terraform_generator/
│       ├── __init__.py
│       ├── config.py              # Pydantic settings
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py          # Architecture, InfrastructureResource, etc.
│       │   └── exceptions.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── loader.py          # Load JSON from path or content
│       │   └── events.py          # Event payload types
│       ├── input/
│       │   ├── __init__.py
│       │   ├── validator.py       # Validate JSON against input_v1.json
│       │   └── analyzer.py        # Analyze recursos; map servico/config to resources
│       ├── normalization/
│       │   ├── __init__.py
│       │   ├── normalizer.py     # Raw → domain model
│       │   └── resolver.py      # Dependency resolution
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── validator.py     # JSON Schema + custom rules
│       │   └── rules.py         # Custom validation rules
│       ├── terraform/
│       │   ├── __init__.py
│       │   ├── template_selector.py  # Map resources to templates
│       │   ├── generator.py          # Render templates
│       │   └── writer.py             # Write .tf files to disk
│       ├── events/
│       │   ├── __init__.py
│       │   ├── publisher.py     # Publish events
│       │   ├── consumer.py     # Consume events, orchestrate pipeline
│       │   └── payloads.py     # Event payload dataclasses
│       └── main.py             # Entry point, worker loop
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_parsing.py
│   │   ├── test_extraction.py
│   │   ├── test_normalization.py
│   │   ├── test_validation.py
│   │   └── test_generator.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── fixtures/
│       └── sample_inputs/
│           ├── web_app.json
│           ├── vibe_economica_only.json
│           ├── vibe_performance_only.json
│           ├── multi_recursos.json
│           ├── invalid_missing_analise.json
│           └── invalid_unsupported_service.json
└── scripts/
    └── run_worker.py
```

### Module Responsibilities

| Package | Responsibility |
|---------|----------------|
| `domain` | Pure domain models, no I/O |
| `ingestion` | Load JSON; emit/consume ingest events |
| `input` | Validate JSON structure; analyze recursos; map to resource list |
| `normalization` | Build domain model from analyzed resources; resolve dependencies |
| `validation` | Domain JSON Schema + custom rules |
| `terraform` | Template selection, rendering, file writing |
| `events` | Event publishing, consumption, orchestration |

---

## JSON Input Contract (V1)

### Input Schema

The service receives **JSON** as the primary input. The structure is defined in `schemas/input_v1.json`.

**Required field:**
- `analise_entrada` (string): Summary of what was detected/analyzed from the original request.

**Optional vibe blocks:**
- `vibe_economica`: Cost-optimized infrastructure option.
- `vibe_performance`: Performance-optimized infrastructure option.

Each vibe contains:
- `descricao` (string): Description of the option.
- `custo_estimado` (string): Estimated cost.
- `recursos` (array): List of requested resources. Each resource has:
  - `servico` (string, required): Service identifier (e.g., `aws_s3_bucket`, `aws_instance`).
  - `config` (string or object, optional): Configuration for the service.

### Example: Full Input

```json
{
  "analise_entrada": "Web application with static assets, security group, and compute",
  "vibe_economica": {
    "descricao": "Cost-optimized web app",
    "custo_estimado": "~$25/month",
    "recursos": [
      {
        "servico": "aws_s3_bucket",
        "config": {
          "bucket": "my-app-assets",
          "tags": { "Environment": "production", "Project": "web-app" }
        }
      },
      {
        "servico": "aws_instance",
        "config": {
          "ami": "ami-0c55b159cbfafe1f0",
          "instance_type": "t3.micro",
          "tags": { "Role": "web" }
        }
      }
    ]
  },
  "vibe_performance": {
    "descricao": "Performance-optimized",
    "custo_estimado": "~$80/month",
    "recursos": [
      {
        "servico": "aws_instance",
        "config": {
          "ami": "ami-0c55b159cbfafe1f0",
          "instance_type": "t3.small",
          "tags": { "Tier": "performance" }
        }
      }
    ]
  }
}
```

### Validation Behavior

- **JSON structure:** Must validate against `schemas/input_v1.json`. Missing `analise_entrada` or malformed structure → validation error.
- **Service names:** Each `servico` in `recursos` must be in the V1 allowed list. Unknown services → validation error.
- **Config:** Each resource's `config` must satisfy the requirements for that service type (e.g., `aws_s3_bucket` requires `bucket`).

### Vibe Selection

The pipeline must determine which vibe(s) to use for Terraform generation. V1 may use a single vibe (e.g., `vibe_economica` only) or merge resources from both, per implementation decision. The documentation should be updated when the selection strategy is finalized.

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

- Project setup (pyproject.toml, venv, ruff)
- Folder structure
- Domain models (Pydantic/dataclasses)
- JSON Schema (`architecture_v1.json`)
- Config (Pydantic Settings)

### Phase 2: JSON Ingestion & Validation (Week 2)

- JSON loader (file path or content)
- Input schema validation (`input_v1.json`)
- Service analysis from `recursos`
- Unit tests for ingestion and validation

### Phase 3: Normalization & Validation (Week 3)

- Normalizer (raw → domain model)
- Dependency resolver
- JSON Schema validator
- Custom validation rules

### Phase 4: Terraform Generation (Week 4)

- Template files for V1 resource types
- Template selector
- Generator (Jinja2)
- File writer

### Phase 5: Event Pipeline (Week 5)

- Event payload types
- In-memory/synchronous pipeline (no broker initially)
- Orchestrator that chains stages
- Output emission (files + optional stdout)

### Phase 6: Event Bus Integration (Week 6)

- Event broker adapter (Redis or RabbitMQ)
- Consumer loop
- Publisher
- Integration tests

### Phase 7: Polish (Week 7)

- Error handling, logging
- Documentation
- Sample architectures
- README and usage examples

---

## Detailed Checklist

### Project Setup
- [ ] Create `pyproject.toml` with dependencies
- [ ] Create `requirements.txt` (or use uv/poetry)
- [ ] Set up `src/terraform_generator` package
- [ ] Configure ruff (or black + isort)
- [ ] Add pre-commit hooks (optional)

### Domain
- [ ] Define `Architecture` model
- [ ] Define `InfrastructureResource` model
- [ ] Define `ArchitectureMetadata` model
- [ ] Define domain exceptions

### Schema
- [ ] Create `schemas/architecture_v1.json`
- [ ] Include all V1 resource types in enum
- [ ] Add `$defs` for nested structures

### Ingestion
- [ ] Implement `Loader` (file path → JSON string or dict)
- [ ] Implement content-based loading (string in, parsed JSON out)
- [ ] Handle file-not-found, encoding, and JSON parse errors

### JSON Validation
- [ ] Load and validate against `schemas/input_v1.json`
- [ ] Reject malformed structure (missing `analise_entrada`, invalid `recursos`)
- [ ] Return clear validation errors with path/field info

### Service Analysis
- [ ] Iterate over `vibe_economica.recursos` and `vibe_performance.recursos`
- [ ] Interpret `servico` to map to Terraform resource type
- [ ] Interpret `config` (string or object) into resource attributes
- [ ] Produce analyzed resource list for normalization

### Normalization
- [ ] Map analyzed resources to `InfrastructureResource`
- [ ] Resolve `dependencies` from references
- [ ] Validate no circular dependencies
- [ ] Build `Architecture` root

### Validation
- [ ] Load JSON Schema
- [ ] Validate domain model (as dict) against schema
- [ ] Implement custom rules (circular deps, undefined refs)
- [ ] Collect errors and warnings
- [ ] Emit validation result

### Terraform
- [ ] Create Jinja2 templates for each V1 resource type
- [ ] Implement template selector
- [ ] Implement generator (render with resource data)
- [ ] Implement writer (write to output directory)
- [ ] Generate `main.tf` with provider block

### Events
- [ ] Define event payload dataclasses
- [ ] Implement synchronous pipeline (no broker)
- [ ] Chain: ingest → parse → extract → normalize → validate → select → generate → output
- [ ] Emit `architecture.processing.completed` on success
- [ ] Emit `architecture.processing.failed` on error

### Event Bus (Optional for V1)
- [ ] Choose broker (Redis Streams / RabbitMQ)
- [ ] Implement publisher
- [ ] Implement consumer
- [ ] Wire consumer to pipeline

### Testing
- [ ] Unit tests for JSON ingestion and validation
- [ ] Unit tests for service analysis
- [ ] Unit tests for normalizer
- [ ] Unit tests for validator
- [ ] Unit tests for generator
- [ ] Integration test: sample JSON → Terraform output

### Documentation
- [ ] README with quick start
- [ ] Sample architecture file
- [ ] Usage examples

---

## Risks and Edge Cases

| Risk | Mitigation |
|------|------------|
| **JSON structure varies** | Validate strictly against `input_v1.json`; fail fast with clear errors |
| **Config format varies** | Define expected `config` shape per `servico`; validate before normalization |
| **Circular dependencies** | Validate in normalization; reject with clear error |
| **Large files** | Set size limit (e.g., 1MB); stream if needed later |
| **Unicode in Markdown** | Use UTF-8 throughout; validate encoding |
| **Template rendering errors** | Wrap in try/except; emit `architecture.processing.failed` with template error |
| **Output directory exists** | Overwrite or use unique subdir per `correlation_id` |
| **Partial artifact upload** | Log partial uploads; emit failure event with `partial_uploads` list (see [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md)) |

### Edge Cases to Handle

1. **Empty architecture:** No resources → warning, generate empty `main.tf` only
2. **Duplicate logical names:** Validation error
3. **Invalid AMI/region:** Out of scope for V1; pass through to Terraform (will fail at apply)
4. **Malformed JSON in attributes:** Extraction or validation error

---

## Future Roadmap

| Feature | Description | When |
|---------|-------------|------|
| Terraform execution | `terraform plan` / `apply` via subprocess or API | Post-V1 |
| Multi-provider | GCP, Azure support | Post-V1 |
| List-style extraction | Parse "bucket: name (tags)" from lists | Phase 2+ |
| Drift detection | Compare generated vs applied state | Post-execution |
| Template customization | User-provided templates | Post-V1 |
| REST API | HTTP endpoint for sync processing | Post-V1 |
| Webhook notifications | Notify on completion/failure | Post-V1 |
| State backend config | S3 backend for Terraform state | With execution |
| Artifact storage | Upload generated Terraform to Cloudflare (S3-compatible) | See [ARTIFACT_STORAGE.md](./ARTIFACT_STORAGE.md) |

---

## Summary

This PDD defines a narrow, achievable V1: ingest JSON → validate structure → analyze services → normalize → validate domain model → generate Terraform. The design is event-driven, provider-aware, and template-based. The input contract is JSON with `analise_entrada` and optional `vibe_economica`/`vibe_performance` blocks containing `recursos`. Implementation can proceed phase-by-phase with clear checkpoints. Terraform execution is explicitly out of scope.

Future Cursor prompts can reference this document and implement one stage at a time, preserving architectural consistency.
