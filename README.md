# Factory Output
Este repositório contém os sistemas gerados automaticamente pela [Fábrica de Agentes IA](https://github.com/EddieDevLife/factory-IA).

## Métricas (GitHub Pages + SQL opcional)

Este repo também publica métricas agregadas das entregas em `entregas/` para facilitar monitoramento e BI.

**Saídas geradas (GitHub Pages)**
- `site/deliveries_index.json`: índice das entregas + campos principais (status, tempo, modelos, etc.).
- `site/runs.csv`: o mesmo em CSV (pronto para Tableau/Databricks/Deepnote).

**Como funciona**
- Workflow: `.github/workflows/metrics.yml`
- Exportador: `scripts/export_metrics.py`
- Ingest (opcional): `scripts/ingest_postgres.py` (Postgres via `DATABASE_URL`)

### Habilitar GitHub Pages
1. Em `Settings → Pages` do repositório, selecione **Source: GitHub Actions**.
2. Faça um push no `main` (o workflow vai publicar o `site/` automaticamente).

### SQL gratuito (recomendação)
Recomendado: **Postgres no Neon (free tier)**.

Para habilitar ingest no banco:
1. Crie um banco Postgres no Neon e copie a connection string.
2. No GitHub, configure o secret do repo `agentix-vault`: `Settings → Secrets and variables → Actions → New repository secret`
   - Name: `DATABASE_URL`
   - Value: sua connection string do Neon
3. Rode o workflow manualmente (`Actions → Vault metrics → Run workflow`) ou aguarde a próxima execução.

Tabela criada (se não existir): `vault_deliveries`.

### Rodar localmente (opcional)
- Exportar site: `python3 scripts/export_metrics.py`
- Ingest (precisa `DATABASE_URL`):
  - `python3 -m pip install -r scripts/requirements.txt`
  - `DATABASE_URL='...' python3 scripts/ingest_postgres.py`
