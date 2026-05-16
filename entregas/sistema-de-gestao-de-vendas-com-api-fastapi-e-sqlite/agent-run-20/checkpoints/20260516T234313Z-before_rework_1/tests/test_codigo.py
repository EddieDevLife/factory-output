import sys
import subprocess
import importlib.util
import os
from datetime import datetime
import pytest
from fastapi.testclient import TestClient


# Teste subprocess para o comportamento CLI do script sem argumentos e com help

def test_cli_no_args():
    result = subprocess.run(
        [sys.executable, "output/sistema_gerado.py"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "Sistema de Gestao de Vendas" in result.stdout


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "output/sistema_gerado.py", "-h"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "Use --serve" in result.stdout


@pytest.fixture
def client(tmp_path):
    # Importa o modulo dinamicamente alterando o DB path para tmp_path
    import sys
    import builtins
    module_name = "sistema_gerado"
    module_path = os.path.abspath("output/sistema_gerado.py")

    # Força recarregar o módulo para isolar o db path para este teste
    if module_name in sys.modules:
        del sys.modules[module_name]

    # Patchar a variável SISTEMA_DB_PATH antes de importar
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    # Intercepta o sistema para alterar SISTEMA_DB_PATH para outro arquivo temporário
    setattr(module, "SISTEMA_DB_PATH", str(tmp_path / "test_vendas.db"))
    # Precisa recrear engine, session e Base.tables após mudar caminho
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import sqlalchemy

    module.SQLALCHEMY_DATABASE_URL = f"sqlite:///{module.SISTEMA_DB_PATH}"
    module.engine = create_engine(module.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=module.engine)
    # Recreate tables
    module.Base.metadata.create_all(bind=module.engine)

    # Execute a startup configs
    spec.loader.exec_module(module)

    app = module.app
    client = TestClient(app)
    return client, module


def test_criar_venda(client):
    client_app, module = client
    venda_payload = {
        "item": "Caneta",
        "quantidade": 10,
        "valor_unitario": 2.5,
        "data_venda": "2023-01-01T10:00:00"
    }
    response = client_app.post("/vendas", json=venda_payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["item"] == venda_payload["item"]
    assert json_data["quantidade"] == venda_payload["quantidade"]
    assert float(json_data["valor_unitario"]) == venda_payload["valor_unitario"]


def test_listar_vendas_vazio(client):
    client_app, module = client
    response = client_app.get("/vendas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_cria_e_lista_vendas(client):
    client_app, module = client
    vendas = [
        {"item": "Lapis", "quantidade": 5, "valor_unitario": 1.0, "data_venda": "2023-01-02T09:00:00"},
        {"item": "Borracha", "quantidade": 2, "valor_unitario": 0.5, "data_venda": "2023-01-02T09:01:00"}
    ]
    for venda in vendas:
        response = client_app.post("/vendas", json=venda)
        assert response.status_code == 201

    response = client_app.get("/vendas")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == len(vendas)


def test_consultar_venda_existente(client):
    client_app, module = client
    venda = {"item": "Caderno", "quantidade": 3, "valor_unitario": 5.0, "data_venda": "2023-01-03T12:00:00"}
    create_resp = client_app.post("/vendas", json=venda)
    assert create_resp.status_code == 201
    venda_id = create_resp.json()["id"]

    get_resp = client_app.get(f"/vendas/{venda_id}")
    assert get_resp.status_code == 200
    json_data = get_resp.json()
    assert json_data["id"] == venda_id
    assert json_data["item"] == venda["item"]


def test_consultar_venda_inexistente(client):
    client_app, module = client
    response = client_app.get("/vendas/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Venda não encontrada"


def test_atualizar_venda(client):
    client_app, module = client
    venda = {"item": "Mouse", "quantidade": 1, "valor_unitario": 50.0, "data_venda": "2023-02-01T08:00:00"}
    create_resp = client_app.post("/vendas", json=venda)
    venda_id = create_resp.json()["id"]

    update_payload = {"quantidade": 3, "valor_unitario": 45.0}
    update_resp = client_app.put(f"/vendas/{venda_id}", json=update_payload)
    assert update_resp.status_code == 200
    json_data = update_resp.json()
    assert json_data["quantidade"] == 3
    assert float(json_data["valor_unitario"]) == 45.0


def test_atualizar_venda_inexistente(client):
    client_app, module = client
    update_payload = {"quantidade": 5}
    response = client_app.put("/vendas/99999", json=update_payload)
    assert response.status_code == 404


def test_remover_venda(client):
    client_app, module = client
    venda = {"item": "Teclado", "quantidade": 1, "valor_unitario": 70.0, "data_venda": "2023-03-01T09:00:00"}
    create_resp = client_app.post("/vendas", json=venda)
    venda_id = create_resp.json()["id"]

    delete_resp = client_app.delete(f"/vendas/{venda_id}")
    assert delete_resp.status_code == 204

    # Confirmar que venda foi removida
    get_resp = client_app.get(f"/vendas/{venda_id}")
    assert get_resp.status_code == 404


def test_remover_venda_inexistente(client):
    client_app, module = client
    response = client_app.delete("/vendas/99999")
    assert response.status_code == 404


def test_validacoes_criacao(client):
    client_app, module = client
    invalid_payloads = [
        {"item": "Caneta", "quantidade": 0, "valor_unitario": 2.5, "data_venda": "2023-01-01T10:00:00"},
        {"item": "Caneta", "quantidade": 1, "valor_unitario": 0.0, "data_venda": "2023-01-01T10:00:00"},
        {"item": "Caneta", "quantidade": -1, "valor_unitario": 2.5, "data_venda": "2023-01-01T10:00:00"}
    ]
    for payload in invalid_payloads:
        resp = client_app.post("/vendas", json=payload)
        assert resp.status_code == 422


def test_validacoes_atualizacao(client):
    client_app, module = client
    venda = {"item": "Caneta", "quantidade": 1, "valor_unitario": 2.5, "data_venda": "2023-01-01T10:00:00"}
    create_resp = client_app.post("/vendas", json=venda)
    venda_id = create_resp.json()["id"]

    invalid_updates = [
        {"quantidade": 0},
        {"valor_unitario": 0},
        {"quantidade": -5},
        {"valor_unitario": -1}
    ]

    for upd in invalid_updates:
        resp = client_app.put(f"/vendas/{venda_id}", json=upd)
        assert resp.status_code == 422

