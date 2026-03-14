# Terraform Generator Service — Prompt-Driven Development Document

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** 2025-03-14

---

## Overview

The **Terraform Generator Service** is a Python event-driven backend service that ingests architecture definitions written in Markdown, parses them into structured infrastructure requirements, normalizes them into a JSON-Schema-aligned internal representation, validates the result, and generates Terraform configuration files from AWS-oriented templates.

The service does **not** execute Terraform. It produces ready-to-use `.tf` files that can be applied by external tooling (e.g., CI/CD, Terraform Cloud, or manual `terraform apply`).

### Service Purpose (One-Liner)

*Parse Markdown architecture definitions → normalize into validated JSON-Schema-aligned domain model → generate AWS Terraform files from templates.*

---

## Objective

**Primary goal:** Build a Python event-driven service that receives architecture definitions in Markdown files, parses the infrastructure requirements, normalizes them into a JSON-Schema-aligned internal representation, and generates Terraform files from AWS-oriented templates.

**Success criteria for V1:**
- Markdown architecture files can be ingested and parsed
- Parsed content is normalized into a provider-aware domain model
- Normalized output validates against a defined JSON Schema
- Terraform files are generated from templates for supported AWS resource types
- The pipeline is event-driven with clear stage boundaries

---

## V1 Scope

| In Scope | Description |
|----------|-------------|
| Markdown ingestion | Accept `.md` files as input (file path or content) |
| Markdown parsing | Extract infrastructure-related sections and blocks |
| Requirement extraction | Identify AWS resource types, names, and attributes from parsed content |
| Normalization | Convert extracted data into internal domain model |
| JSON Schema validation | Validate normalized output against schema |
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

1. **Input format:** Architecture descriptions follow a predictable Markdown structure (headings, code blocks, lists) that can be parsed programmatically.
2. **AWS focus:** All V1 resources map to AWS provider (`hashicorp/aws`); no multi-provider logic.
3. **Event broker:** An event bus (e.g., Redis Streams, RabbitMQ, or SQS) is available; exact choice is configurable.
4. **Python version:** Python 3.11+ for type hints and modern syntax.
5. **Terraform version:** Generated output targets Terraform 1.x and AWS provider 5.x.
6. **Single-tenant processing:** Each event represents one architecture file; no batching of multiple files per event.
7. **Idempotency:** Re-processing the same input yields the same output (deterministic).
8. **No secrets in Markdown:** Sensitive values (e.g., API keys) are not embedded in architecture files; they are injected at apply time.

---

## Architecture

### High-Level Stages

The system is organized into eight conceptual stages, each with clear inputs and outputs:

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│  1. Ingestion   │→│  2. Parsing     │→│  3. Extraction          │
│  (Markdown in)  │ │  (AST / blocks) │ │  (Raw requirements)     │
└─────────────────┘ └─────────────────┘ └───────────┬─────────────┘
                                                    │
┌─────────────────┐ ┌─────────────────┐ ┌─────────▼─────────────┐
│  8. Output      │←│  7. Generation   │←│  4. Normalization      │
│  (Events/files) │ │  (Terraform)     │ │  (Domain model)        │
└─────────────────┘ └─────────────────┘ └───────────┬─────────────┘
                                                    │
                              ┌─────────────────────▼─────────────────────┐
                              │  5. Validation (JSON Schema)              │
                              └─────────────────────┬─────────────────────┘
                                                    │
                              ┌─────────────────────▼─────────────────────┐
                              │  6. Template Selection                    │
                              └───────────────────────────────────────────┘
```

### Stage Responsibilities

| Stage | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| **1. Ingestion** | Receive Markdown (path or content), load raw text | Event with file path or content | Raw Markdown string |
| **2. Parsing** | Parse Markdown into structured blocks (headings, code blocks, lists) | Raw Markdown | Parsed document structure |
| **3. Extraction** | Extract infrastructure requirements from parsed blocks | Parsed document | Raw requirement records |
| **4. Normalization** | Map raw records to domain model, resolve references | Raw requirements | Normalized domain model |
| **5. Validation** | Validate against JSON Schema, collect errors/warnings | Domain model (as dict) | Validation result |
| **6. Template Selection** | Map domain entities to template IDs | Domain model | Template mapping list |
| **7. Generation** | Render Terraform from templates with domain data | Template mapping + domain model | Terraform file content |
| **8. Output** | Emit events, write files, return response | Generated Terraform | Published events, files |

### Layering

- **Ingestion / Event handling:** Adapter layer (file system, message queue)
- **Parsing / Extraction:** Application services (orchestration)
- **Normalization / Validation:** Domain layer (business rules)
- **Template selection / Generation:** Application services (Terraform-specific)
- **Output:** Adapter layer (file system, event publishing)

---

## Event Flow

### Event Naming Convention

Events use a `{domain}.{action}.{result}` pattern:

| Event Name | Trigger | Payload |
|------------|---------|---------|
| `architecture.ingest.requested` | External request to process a file | `{ "file_path": "...", "correlation_id": "..." }` |
| `architecture.parsed` | Parsing complete | `{ "correlation_id", "parsed_document": {...} }` |
| `architecture.extracted` | Extraction complete | `{ "correlation_id", "raw_requirements": [...] }` |
| `architecture.normalized` | Normalization complete | `{ "correlation_id", "domain_model": {...} }` |
| `architecture.validated` | Validation complete | `{ "correlation_id", "valid": bool, "errors": [], "warnings": [] }` |
| `architecture.templates.selected` | Template selection complete | `{ "correlation_id", "template_mappings": [...] }` |
| `architecture.terraform.generated` | Generation complete | `{ "correlation_id", "terraform_files": [{ "path": "...", "content": "..." }] }` |
| `architecture.processing.completed` | Full pipeline success | `{ "correlation_id", "output_path": "...", "summary": {...} }` |
| `architecture.processing.failed` | Pipeline failure | `{ "correlation_id", "stage": "...", "error": "..." }` |

### Correlation ID

Every event in a pipeline shares the same `correlation_id` to enable tracing and debugging.

### Event Flow Diagram

```
architecture.ingest.requested
        │
        ▼
   [Ingestion] ──► architecture.parsed
        │
        ▼
   [Parsing] ──► architecture.extracted
        │
        ▼
   [Extraction] ──► architecture.normalized
        │
        ▼
   [Normalization] ──► architecture.validated
        │
        ▼
   [Validation] ──► architecture.templates.selected
        │
        ▼
   [Template Selection] ──► architecture.terraform.generated
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
    "source_file": "architectures/web-app.md",
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

### Schema Location

- Schema file: `schemas/architecture_v1.json`
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

Generated files are placed in an output directory (configurable):

```
output/{correlation_id}/
├── main.tf           # Provider + backend (optional)
├── variables.tf       # Input variables (if any)
├── s3_bucket.tf       # One file per resource type group (or per resource)
├── instance.tf
├── security_group.tf
└── ...
```

**Alternative (simpler for V1):** One `.tf` file per resource, e.g. `assets_bucket.tf`, `web_server.tf`.

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
│   └── architecture_v1.json
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
│       │   ├── loader.py          # Load Markdown from path or content
│       │   └── events.py          # Event payload types
│       ├── parsing/
│       │   ├── __init__.py
│       │   ├── markdown_parser.py # Parse MD to structured blocks
│       │   └── blocks.py         # Block types (heading, code, list)
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── extractor.py      # Extract raw requirements from blocks
│       │   └── patterns.py      # Regex/pattern definitions
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
│       └── sample_architectures/
│           └── web_app.md
└── scripts/
    └── run_worker.py
```

### Module Responsibilities

| Package | Responsibility |
|---------|----------------|
| `domain` | Pure domain models, no I/O |
| `ingestion` | Load Markdown; emit/consume ingest events |
| `parsing` | Convert Markdown text to structured blocks |
| `extraction` | Extract raw infrastructure records from blocks |
| `normalization` | Build domain model; resolve dependencies |
| `validation` | JSON Schema + custom rules |
| `terraform` | Template selection, rendering, file writing |
| `events` | Event publishing, consumption, orchestration |

---

## Markdown Input Patterns (V1)

### Supported Structure

V1 expects architecture documents with:

1. **Headings** to denote sections (e.g., `## S3 Buckets`, `## Compute`)
2. **Code blocks** with `terraform` or `hcl` language tag for resource definitions
3. **Lists** for simple resource listings (e.g., bucket names)

### Example 1: Code Block Style

```markdown
# Web Application Architecture

## S3 Buckets

We need an S3 bucket for static assets.

```terraform
resource "aws_s3_bucket" "assets_bucket" {
  bucket = "my-app-assets"
  tags = {
    Environment = "production"
    Project     = "web-app"
  }
}
```

## Compute

```terraform
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  tags = {
    Role = "web"
  }
}
```
```

### Example 2: Declarative List Style

```markdown
# Simple Storage Architecture

## Buckets

- assets_bucket: my-app-assets (Environment=production)
- logs_bucket: my-app-logs (Environment=production)
```

The extractor must recognize both styles. **V1 priority:** Start with code block style (Example 1) as it is more explicit and easier to parse. Add list style in a later phase if needed.

### Example 3: Section-Based with Inline HCL

```markdown
## Security Groups

### Web SG

- Name: web-sg
- Description: Security group for web servers
- Ingress: port 80 from 0.0.0.0/0
```

The extractor may support a simplified key-value format under headings. **V1:** Focus on HCL code blocks first.

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

- Project setup (pyproject.toml, venv, ruff)
- Folder structure
- Domain models (Pydantic/dataclasses)
- JSON Schema (`architecture_v1.json`)
- Config (Pydantic Settings)

### Phase 2: Parsing & Extraction (Week 2)

- Markdown parser (blocks: headings, code blocks)
- Extractor for HCL code blocks
- Unit tests for parsing and extraction

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
- [ ] Implement `Loader` (file path → Markdown string)
- [ ] Implement content-based loading (string in, string out)
- [ ] Handle file-not-found and encoding errors

### Parsing
- [ ] Integrate Markdown parser (markdown-it-py or mistune)
- [ ] Define block types (Heading, CodeBlock, List)
- [ ] Extract headings with levels
- [ ] Extract code blocks with language tag

### Extraction
- [ ] Detect `terraform`/`hcl` code blocks
- [ ] Parse HCL-like content (or use minimal regex for V1)
- [ ] Extract `resource "type" "name"` patterns
- [ ] Extract attributes (key = value)
- [ ] Produce raw requirement records

### Normalization
- [ ] Map raw records to `InfrastructureResource`
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
- [ ] Unit tests for parser
- [ ] Unit tests for extractor
- [ ] Unit tests for normalizer
- [ ] Unit tests for validator
- [ ] Unit tests for generator
- [ ] Integration test: sample MD → Terraform output

### Documentation
- [ ] README with quick start
- [ ] Sample architecture file
- [ ] Usage examples

---

## Risks and Edge Cases

| Risk | Mitigation |
|------|------------|
| **Markdown format varies** | Start with strict patterns; document supported format; fail fast with clear errors |
| **HCL in code blocks is complex** | V1: Use regex or simple parsing for `resource "x" "y"` and key=value; avoid full HCL parser initially |
| **Circular dependencies** | Validate in normalization; reject with clear error |
| **Large files** | Set size limit (e.g., 1MB); stream if needed later |
| **Unicode in Markdown** | Use UTF-8 throughout; validate encoding |
| **Template rendering errors** | Wrap in try/except; emit `architecture.processing.failed` with template error |
| **Output directory exists** | Overwrite or use unique subdir per `correlation_id` |

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

---

## Summary

This PDD defines a narrow, achievable V1: ingest Markdown → parse → extract → normalize → validate → generate Terraform. The design is event-driven, provider-aware, and template-based. Implementation can proceed phase-by-phase with clear checkpoints. Terraform execution is explicitly out of scope.

Future Cursor prompts can reference this document and implement one stage at a time, preserving architectural consistency.
