# Terraform Generator Service

Serviço em Python orientado a eventos que recebe **entrada JSON** descrevendo opções de infraestrutura (vibes), valida a estrutura e os serviços solicitados, normaliza o conteúdo em uma representação interna alinhada a JSON-Schema e gera arquivos de configuração Terraform a partir de templates voltados para AWS (até o momento).

**Objetivo:** Automatizar a geração de arquivos Terraform para AWS a partir de definições de arquitetura de alto nível. O serviço não executa Terraform — ele produz arquivos `.tf` prontos para uso por ferramentas externas (CI/CD, Terraform Cloud ou `terraform apply` manual).

---

## Membros da equipe

- **Laisa Rio**
- **Lucas Procopio**
- **Paulo Boccaletti**

---

## Onde o projeto está hospedado

O serviço está disponível em produção no **Railway**:

**URL:** https://terraform-generator-service-production.up.railway.app

O repositório está no **GitHub**. Para clonar:

```bash
git clone https://github.com/<sua-org>/terraform-generator-service.git
cd terraform-generator-service
```

---

## Configuração

### Pré-requisitos

- Python 3.10+
- pip

### Instalação

```bash
# Crie e ative um ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instale em modo editável
pip install -e .

# Opcional: instale dependências de desenvolvimento para testes
pip install -e ".[dev]"
```

### Variáveis de ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

Edite o `.env` com seus valores. Para **desenvolvimento local**, `ENVIRONMENT=dev` é suficiente (não precisa de credenciais S3). Para **produção** (upload para S3), configure:

| Variável | Descrição |
|----------|------------|
| `ENVIRONMENT` | `dev` (apenas local) ou `production` (upload para S3) |
| `S3_API` | URL do endpoint da API S3-compatível (ex.: Cloudflare R2) |
| `AWS_ACCESS_KEY_ID` | Chave de acesso para S3 |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta para S3 |
| `LOG_LEVEL` | Opcional: `DEBUG`, `INFO`, `WARNING`, `ERROR` (padrão: `INFO`) |

---

## Uso

### CLI

```bash
# Processar um arquivo JSON (especifique qual vibe gerar)
terraform-generator --decision vibe_economica caminho/para/input.json
terraform-generator --decision vibe_performance caminho/para/input.json

# Sem --decision: ambas as vibes são processadas (retrocompatível)
terraform-generator caminho/para/input.json

# Ler da entrada padrão
cat input.json | terraform-generator --decision vibe_economica --stdin

# Especificar diretório de saída (padrão: output/)
terraform-generator -o ./minha-saida --decision vibe_economica caminho/para/input.json
```

**Saída:** Os arquivos Terraform são gravados em `output/{correlation_id}/` (ou no diretório especificado com `-o`).

### Formato de entrada

A entrada deve ser um **array JSON não vazio**. Cada item deve conter um objeto `output` com o payload da arquitetura:

```json
[
  {
    "output": {
      "analise_entrada": "Descrição do projeto...",
      "vibe_economica": {
        "descricao": "...",
        "recursos": [
          { "servico": "aws_s3_bucket", "config": { "bucket": "meu-bucket" } }
        ]
      },
      "vibe_performance": { ... }
    }
  }
]
```

Veja exemplos em `tests/fixtures/sample_inputs/`.

### API (FastAPI)

Inicie o servidor da API:

```bash
uvicorn terraform_generator.api:app --reload --port 8000
```

#### Chamando `/api/process`

**Método:** `POST`  
**URL local:** `http://localhost:8000/api/process`  
**URL em produção:** `https://terraform-generator-service-production.up.railway.app/api/process`

**Corpo da requisição (JSON):**

```json
{
  "event_id": "ev-123",
  "project_id": "proj-456",
  "json_url_r2": "https://seu-storage.exemplo.com/caminho/para/arquitetura.json",
  "sent_at": "2025-03-14T12:00:00Z",
  "decision": "vibe_economica"
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `event_id` | string | Identificador do evento |
| `project_id` | string | Identificador do projeto |
| `json_url_r2` | string | URL para buscar a definição JSON da arquitetura (R2/S3 ou qualquer URL HTTP) |
| `sent_at` | string | Data/hora em que o evento foi enviado |
| `decision` | string | `vibe_economica` ou `vibe_performance` — qual vibe gerar |

**Resposta de sucesso (200):**

```json
{
  "success": true,
  "correlation_id": "uuid",
  "output_path": "output/uuid/",
  "summary": { "resources": 3, "files": 4 }
}
```

**Resposta de erro (422):**

```json
{
  "success": false,
  "correlation_id": "uuid",
  "stage": "input_validation",
  "error": "Mensagem de erro"
}
```

O JSON em `json_url_r2` pode ser um **array** `[{ "output": {...} }]` ou um **objeto** `{ "output": {...} }` / `{ "analise_entrada": "...", "vibe_economica": {...}, ... }`. A API normaliza ambos os formatos.

---

## Escopo V1

- **Entrada:** Array JSON com itens contendo `output` (com `analise_entrada` e blocos opcionais `vibe_economica`/`vibe_performance` e `recursos`)
- **Saída:** Arquivos Terraform (`.tf`) para recursos AWS
- **Recursos suportados:** `aws_s3_bucket`, `aws_s3_bucket_versioning`, `aws_instance`, `aws_security_group`, `aws_vpc`, `aws_subnet`

---

## Visão geral da arquitetura

```
Entrada JSON (array) → Ingestão → Validação → Extração do output → Análise de serviços → Normalização → Validação do domínio → Geração → Arquivos Terraform
```

Veja [docs/PDD.md](docs/PDD.md) para a arquitetura completa, fluxo de eventos e modelo de domínio.

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [docs/PDD.md](docs/PDD.md) | Especificação completa de Prompt-Driven Development |
| [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) | Fases e marcos de implementação |
| [docs/DEVELOPMENT_CHECKLIST.md](docs/DEVELOPMENT_CHECKLIST.md) | Checklist de implementação |
| [docs/PROMPT_GUIDE.md](docs/PROMPT_GUIDE.md) | Guia para implementação feature a feature |

---

## Deploy no Railway

1. Conecte seu repositório GitHub ao Railway.
2. **Se o projeto estiver em um subdiretório**, defina **Root Directory** nas configurações do projeto no Railway.
3. O Railway usará o **Dockerfile** (ou `nixpacks.toml` + Procfile se não houver Dockerfile).
4. Configure as variáveis de ambiente: `ENVIRONMENT`, `S3_API`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (para produção).

### Build local (Docker)

```bash
docker build -t terraform-generator .
docker run -p 8000:8000 -e PORT=8000 terraform-generator
```

---

## Status do projeto

**Status:** V1 completo. Entrada JSON (formato array ou objeto), FastAPI para deploy no Railway, seleção de vibe baseada em decisão.

---

## Licença

Este projeto está licenciado sob a **MIT License**. Veja [LICENSE](LICENSE) para detalhes.
