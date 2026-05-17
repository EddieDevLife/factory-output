# Sistema de Gestão de Vendas (FastAPI + SQLite)

API REST simples para gerenciar **clientes**, **produtos** e **vendas**, com banco **SQLite**.

## Rodar com Docker

```bash
docker compose up --build
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Painel (tester/gestão): `http://127.0.0.1:8000/tester`

### Parar

```bash
docker compose down
```

## Rodar local (sem Docker)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn sistema_gerado:app --reload --host 127.0.0.1 --port 8000
```

