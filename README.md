# Terraform Generator Service

A Python event-driven service that receives **JSON input** describing infrastructure options (vibes), validates the structure and requested services, normalizes the content into a JSON-Schema-aligned internal representation, and generates Terraform configuration files from AWS-oriented templates.

**V1 does not execute Terraform** — it produces ready-to-use `.tf` files for external tooling (CI/CD, Terraform Cloud, or manual `terraform apply`).

---

## Group Members

- **Laisa Rio**
- **Lucas Procopio**
- **Paulo Boccaletti**

---

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository (if not already)
git clone <repository-url>
cd terraform-generator-service

# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .

# Optional: install dev dependencies for testing
pip install -e ".[dev]"
```

### Environment Variables

For local development, no extra configuration is required. For production (S3 uploads):

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | `dev` (local only) or `production` (upload to S3) |
| `S3_API` | S3-compatible API endpoint URL |
| `AWS_ACCESS_KEY_ID` | Access key for S3 |
| `AWS_SECRET_ACCESS_KEY` | Secret key for S3 |

---

## Usage

### CLI

```bash
# Process a JSON input file (specify which vibe to generate)
terraform-generator --decision vibe_economica path/to/input.json
terraform-generator --decision vibe_performance path/to/input.json

# Without --decision: both vibes are processed (backward compatible)
terraform-generator path/to/input.json

# Read from stdin
cat input.json | terraform-generator --decision vibe_economica --stdin

# Specify output directory (default: output/)
terraform-generator -o ./my-output --decision vibe_economica path/to/input.json
```

**Output:** Terraform files are written to `output/{correlation_id}/` (or the directory specified with `-o`).

### Input Format

The root input must be a **non-empty JSON array**. Each item must contain an `output` object with the architecture payload:

```json
[
  {
    "output": {
      "analise_entrada": "Project description...",
      "vibe_economica": {
        "descricao": "...",
        "recursos": [
          { "servico": "aws_s3_bucket", "config": { "bucket": "my-bucket" } }
        ]
      },
      "vibe_performance": { ... }
    }
  }
]
```

See `tests/fixtures/sample_inputs/` for examples.

### API (FastAPI)

```bash
# Start the API server
uvicorn terraform_generator.api:app --reload --port 8000
```

The `/api/process` endpoint requires a `decision` field (`vibe_economica` or `vibe_performance`) in the request body. Only the chosen vibe is used for Terraform generation. See [docs/PDD.md](docs/PDD.md) for details.

---

## V1 Scope

- **In:** JSON array with items containing `output` (with `analise_entrada` and optional `vibe_economica`/`vibe_performance` blocks and `recursos`)
- **Out:** Terraform files (`.tf`) for AWS resources
- **Supported resources:** `aws_s3_bucket`, `aws_s3_bucket_versioning`, `aws_instance`, `aws_security_group`, `aws_vpc`, `aws_subnet`

---

## Architecture Overview

```
JSON Input (array) → Ingestion → Validate → Extract output → Analyze Services → Normalize → Validate Domain → Generate → Terraform Files
```

See [docs/PDD.md](docs/PDD.md) for full architecture, event flow, and domain model.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PDD.md](docs/PDD.md) | Full Prompt-Driven Development specification |
| [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) | Implementation phases and milestones |
| [docs/DEVELOPMENT_CHECKLIST.md](docs/DEVELOPMENT_CHECKLIST.md) | Implementation checklist |
| [docs/PROMPT_GUIDE.md](docs/PROMPT_GUIDE.md) | Guide for feature-by-feature implementation |

---

## Railway Deployment

1. Connect your GitHub repo to Railway.
2. **If the project is in a subdirectory**, set **Root Directory** in Railway project settings to that folder.
3. Railway will use the **Dockerfile** (or `nixpacks.toml` + Procfile if no Dockerfile).
4. Set env vars: `ENVIRONMENT`, `S3_API`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (for production).

### Build local (Docker)

```bash
docker build -t terraform-generator .
docker run -p 8000:8000 -e PORT=8000 terraform-generator
```

---

## Project Status

**Status:** V1 complete. JSON input (array format), FastAPI for Railway deployment.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
