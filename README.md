# Terraform Generator Service

A Python event-driven service that receives **JSON input** describing infrastructure options (vibes), validates the structure and requested services, normalizes the content into a JSON-Schema-aligned internal representation, and generates Terraform configuration files from AWS-oriented templates.

**V1 does not execute Terraform** — it produces ready-to-use `.tf` files for external tooling (CI/CD, Terraform Cloud, or manual `terraform apply`).

---

## Quick Start

```bash
# Install
pip install -e .

# Process a JSON input file
terraform-generator path/to/input.json
# or
python3 -m terraform_generator.main path/to/input.json

# Or read from stdin
cat input.json | terraform-generator --stdin

# Output: Terraform files in output/{correlation_id}/
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PDD.md](docs/PDD.md) | Full Prompt-Driven Development specification |
| [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) | Implementation phases and milestones |
| [docs/DEVELOPMENT_CHECKLIST.md](docs/DEVELOPMENT_CHECKLIST.md) | Implementation checklist |
| [docs/PROMPT_GUIDE.md](docs/PROMPT_GUIDE.md) | Guide for feature-by-feature implementation |

---

## V1 Scope

- **In:** JSON input files (`.json`) with `analise_entrada` and optional `vibe_economica`/`vibe_performance` blocks containing `recursos`
- **Out:** Terraform files (`.tf`) for AWS resources
- **Supported resources:** `aws_s3_bucket`, `aws_s3_bucket_versioning`, `aws_instance`, `aws_security_group`, `aws_vpc`, `aws_subnet`

---

## Architecture Overview

```
JSON Input → Validate Structure → Analyze Services → Normalize → Validate Domain → Generate → Terraform Files
```

See [docs/PDD.md](docs/PDD.md) for full architecture, event flow, and domain model.

---

## Railway Deployment

1. Connect your GitHub repo to Railway.
2. **If the project is in a subdirectory** (e.g. `terraform-generator-service/`), set **Root Directory** in Railway project settings to that folder.
3. Railway will use `nixpacks.toml` to run `pip install .` and the Procfile to start the API.
4. Set env vars: `ENVIRONMENT`, `S3_API`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (for production).

---

## Project Status

**Status:** V1 complete. JSON input, FastAPI for Railway deployment.

---

## License

(Add license when applicable)
# terraform-generator-service
