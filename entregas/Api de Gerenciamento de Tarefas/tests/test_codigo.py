import sys
import subprocess
import importlib
import datetime
import json
import pytest
from fastapi.testclient import TestClient

import output.sistema_gerado as sistema


@pytest.fixture
def client(tmp_path):
    # Override the database path to use a temporary SQLite DB
    sistema.SISTEMA_DB_PATH = str(tmp_path / "test_tarefas.db")
    # Recreate engine and tables with this new DB path
    sistema.engine = sistema.create_engine(f"sqlite:///{sistema.SISTEMA_DB_PATH}", echo=False, connect_args={"check_same_thread": False})
    sistema.criar_bd_e_tabelas()
    client = TestClient(sistema.app)
    yield client


def test_main_help_and_exit():
    # Run without arguments, should print the message and exit with code 0
    result = subprocess.run([sys.executable, "output/sistema_gerado.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "API de Gerenciamento de Tarefas com Prioridade" in result.stdout


def test_create_task_valid(client):
    # Create a valid task
    hoje = datetime.date.today()
    data_futura = (hoje + datetime.timedelta(days=10)).isoformat()
    payload = {
        "titulo": "Tarefa 1",
        "descricao": "Descricao 1",
        "prazo": data_futura,
        "impacto": 5,
        "status": "pendente"
    }
    response = client.post("/tarefas", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == payload["titulo"]
    assert data["descricao"] == payload["descricao"]
    assert data["prazo"] == payload["prazo"]
    assert data["impacto"] == payload["impacto"]
    assert data["status"] == payload["status"]
    assert "id" in data


def test_create_task_invalid_impact(client):
    hoje = datetime.date.today()
    data_futura = (hoje + datetime.timedelta(days=10)).isoformat()
    payload = {
        "titulo": "Tarefa Inv",
        "descricao": "Descricao Inv",
        "prazo": data_futura,
        "impacto": 11,  # inválido, > 10
        "status": "pendente"
    }
    response = client.post("/tarefas", json=payload)
    assert response.status_code == 422


def test_create_task_invalid_prazo(client):
    hoje = datetime.date.today()
    data_passada = (hoje - datetime.timedelta(days=1)).isoformat()
    payload = {
        "titulo": "Tarefa Inv Prazo",
        "descricao": "Descricao Inv Prazo",
        "prazo": data_passada,
        "impacto": 5,
        "status": "pendente"
    }
    response = client.post("/tarefas", json=payload)
    assert response.status_code == 422


def test_create_task_invalid_status(client):
    hoje = datetime.date.today()
    data_futura = (hoje + datetime.timedelta(days=5)).isoformat()
    payload = {
        "titulo": "Tarefa Inv Status",
        "descricao": "Descricao Inv Status",
        "prazo": data_futura,
        "impacto": 5,
        "status": "invalido"
    }
    response = client.post("/tarefas", json=payload)
    assert response.status_code == 422


def test_list_tasks(client):
    # Criar 2 tarefas
    hoje = datetime.date.today()
    d1 = (hoje + datetime.timedelta(days=5)).isoformat()
    d2 = (hoje + datetime.timedelta(days=10)).isoformat()
    t1 = {
        "titulo": "T1",
        "descricao": "D1",
        "prazo": d1,
        "impacto": 3,
        "status": "pendente"
    }
    t2 = {
        "titulo": "T2",
        "descricao": "D2",
        "prazo": d2,
        "impacto": 7,
        "status": "concluído"
    }
    client.post("/tarefas", json=t1)
    client.post("/tarefas", json=t2)

    # Listar todas
    response = client.get("/tarefas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["titulo"] == "T1"
    assert data[1]["titulo"] == "T2"

    # Filtrar por status pendente
    response = client.get("/tarefas", params={"status": "pendente"})
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pendente"

    # Filtrar por status concluído
    response = client.get("/tarefas", params={"status": "concluído"})
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "concluído"


def test_priority_order(client):
    hoje = datetime.date.today()
    # Criar 3 tarefas com diferentes prazos e impactos
    t1 = {
        "titulo": "Tarefa 1",
        "descricao": "desc",
        "prazo": (hoje + datetime.timedelta(days=3)).isoformat(),  # prazo curto
        "impacto": 5,  # impacto médio
        "status": "pendente"
    }
    t2 = {
        "titulo": "Tarefa 2",
        "descricao": "desc",
        "prazo": (hoje + datetime.timedelta(days=10)).isoformat(),  # prazo longo
        "impacto": 9,  # impacto alto
        "status": "pendente"
    }
    t3 = {
        "titulo": "Tarefa 3",
        "descricao": "desc",
        "prazo": (hoje + datetime.timedelta(days=1)).isoformat(),  # prazo muito curto
        "impacto": 4,  # impacto baixo
        "status": "pendente"
    }
    # Create
    client.post("/tarefas", json=t1)
    client.post("/tarefas", json=t2)
    client.post("/tarefas", json=t3)

    response = client.get("/tarefas/prioridade")
    assert response.status_code == 200
    dados = response.json()

    # Calcular manualmente os scores
    def calc_score(impacto, prazo):
        dias = (datetime.date.fromisoformat(prazo) - hoje).days
        return (impacto * 2) - dias

    scores = [calc_score(t["impacto"], t["prazo"]) for t in dados]
    # Verificar ordem decrescente pelo score
    assert scores == sorted(scores, reverse=True)

    # Check that the order matches our expected ranking
    # Calculate scores for our test tasks
    s1 = calc_score(t1["impacto"], t1["prazo"])
    s2 = calc_score(t2["impacto"], t2["prazo"])
    s3 = calc_score(t3["impacto"], t3["prazo"])
    # The order in dados should correspond to descending scores
    expected_order = sorted([(s1, "Tarefa 1"), (s2, "Tarefa 2"), (s3, "Tarefa 3")], key=lambda x: x[0], reverse=True)
    for obj, expected in zip(dados, expected_order):
        assert obj["titulo"] == expected[1]


def test_update_task(client):
    hoje = datetime.date.today()
    data_futura = (hoje + datetime.timedelta(days=10)).isoformat()
    # Criar tarefa
    resp_create = client.post("/tarefas", json={
        "titulo": "Tarefa Update",
        "descricao": "desc",
        "prazo": data_futura,
        "impacto": 5,
        "status": "pendente"
    })
    tarefas = resp_create.json()
    tid = tarefas["id"]

    # Atualizar titulo e status
    novo_titulo = "Título Atualizado"
    novo_status = "concluído"
    resp_update = client.put(f"/tarefas/{tid}", json={"titulo": novo_titulo, "status": novo_status})
    assert resp_update.status_code == 200
    data = resp_update.json()
    assert data["titulo"] == novo_titulo
    assert data["status"] == novo_status


def test_update_task_invalid_data(client):
    hoje = datetime.date.today()
    data_futura = (hoje + datetime.timedelta(days=10)).isoformat()
    # Criar tarefa
    resp_create = client.post("/tarefas", json={
        "titulo": "Tarefa Inv Update",
        "descricao": "desc",
        "prazo": data_futura,
        "impacto": 5,
        "status": "pendente"
    })
    tarefas = resp_create.json()
    tid = tarefas["id"]

    # Atualizar com impacto inválido
    resp_update = client.put(f"/tarefas/{tid}", json={"impacto": 0})
    assert resp_update.status_code == 422

    # Atualizar com prazo passado
    data_passada = (hoje - datetime.timedelta(days=1)).isoformat()
    resp_update = client.put(f"/tarefas/{tid}", json={"prazo": data_passada})
    assert resp_update.status_code == 422

    # Atualizar com status inválido
    resp_update = client.put(f"/tarefas/{tid}", json={"status": "errado"})
    assert resp_update.status_code == 422


def test_update_task_not_found(client):
    # Tentativa de atualizar tarefa inexistente
    resp = client.put("/tarefas/999", json={"titulo": "NA"})
    assert resp.status_code == 404

