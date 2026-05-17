# Sistema de Monitoramento de Preços (Drogaria SP)

Monitora preço de um produto na **Drogaria São Paulo**, salva histórico em **SQLite** e exibe um **dashboard web** com alertas.

## Rodar com Docker

```bash
docker compose up --build
```

- Dashboard: `http://127.0.0.1:8004/dashboard`
- Swagger: `http://127.0.0.1:8004/docs`

O histórico é persistido em volume Docker (pasta `/app/data` no container).

## Rodar local (sem Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn sistema_gerado:app --reload --host 127.0.0.1 --port 8004
```

