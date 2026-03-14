# Terraform Generator Service

A Python event-driven service that receives architecture definitions in Markdown files, parses them into structured infrastructure requirements, normalizes them into a JSON-Schema-aligned internal representation, and generates Terraform configuration files from AWS-oriented templates.

**V1 does not execute Terraform** — it produces ready-to-use `.tf` files for external tooling (CI/CD, Terraform Cloud, or manual `terraform apply`).

---

## Quick Start

```bash
# Install
pip install -e .

# Process an architecture file
terraform-generator path/to/architecture.md
# or
python3 -m terraform_generator.main path/to/architecture.md

# Or read from stdin
cat architecture.md | terraform-generator --stdin

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

- **In:** Markdown architecture files (`.md`)
- **Out:** Terraform files (`.tf`) for AWS resources
- **Supported resources:** `aws_s3_bucket`, `aws_s3_bucket_versioning`, `aws_instance`, `aws_security_group`, `aws_vpc`, `aws_subnet`

---

## Architecture Overview

```
Markdown → Parse → Extract → Normalize → Validate → Template Select → Generate → Terraform Files
```

See [docs/PDD.md](docs/PDD.md) for full architecture, event flow, and domain model.

---

## Project Status

**Status:** V1 implementation complete. Markdown → Terraform pipeline working.

---

## License

(Add license when applicable)
# terraform-generator-service
