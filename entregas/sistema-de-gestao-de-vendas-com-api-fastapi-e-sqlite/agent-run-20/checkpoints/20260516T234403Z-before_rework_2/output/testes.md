import pytest
from fastapi.testclient import TestClient
import output.sistema_gerado as sg

client = TestClient(sg.app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Limpar estado antes de cada teste
    sg._vendas.clear()
    sg._venda_id_counter = 1


def test_raiz():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Sistema de Gestão de Vendas API está no ar."}


def test_criar_e_listar_vendas():
    # Criar venda
    venda_data = {"produto": "Camiseta", "quantidade": 5, "preco_unitario": 20.0}
    response = client.post("/vendas/", json=venda_data)
    assert response.status_code == 201
    venda = response.json()
    assert venda["id"] == 1
    assert venda["produto"] == "Camiseta"
    assert venda["quantidade"] == 5
    assert venda["preco_unitario"] == 20.0

    # Listar vendas deve conter a venda criada
    response = client.get("/vendas/")
    assert response.status_code == 200
    vendas = response.json()
    assert len(vendas) == 1
    assert vendas[0]["id"] == 1


def test_obter_venda_valida():
    # Registrar venda primeiro
    venda_data = {"produto": "Caneca", "quantidade": 3, "preco_unitario": 15.5}
    response = client.post("/vendas/", json=venda_data)
    venda_id = response.json()["id"]

    response = client.get(f"/vendas/{venda_id}")
    assert response.status_code == 200
    venda = response.json()
    assert venda["id"] == venda_id
    assert venda["produto"] == "Caneca"


def test_obter_venda_inexistente():
    response = client.get("/vendas/999")
    assert response.status_code == 404


def test_remover_venda_inexistente():
    response = client.delete("/vendas/999")
    assert response.status_code == 404


def test_remover_venda_existente():
    venda_data = {"produto": "Livro", "quantidade": 1, "preco_unitario": 50.0}
    post_resp = client.post("/vendas/", json=venda_data)
    venda_id = post_resp.json()["id"]

    response = client.delete(f"/vendas/{venda_id}")
    assert response.status_code == 204

    # Verificar se venda foi removida
    get_resp = client.get(f"/vendas/{venda_id}")
    assert get_resp.status_code == 404


def test_validacoes_criacao():
    # quantidade e preco_unitario devem ser > 0
    invalid_data = [
        {"produto": "X", "quantidade": 0, "preco_unitario": 10},
        {"produto": "X", "quantidade": 1, "preco_unitario": 0},
        {"produto": "X", "quantidade": -1, "preco_unitario": 10},
        {"produto": "X", "quantidade": 1, "preco_unitario": -5},
    ]
    for data in invalid_data:
        response = client.post("/vendas/", json=data)
        assert response.status_code == 422


def test_validacoes_atualizacao():
    # Criar venda
    venda_data = {"produto": "Bola", "quantidade": 10, "preco_unitario": 30.0}
    post_resp = client.post("/vendas/", json=venda_data)
    venda_id = post_resp.json()["id"]

    # Atualizar com dados válidos
    update_data = {"quantidade": 15, "preco_unitario": 35.0}
    put_resp = client.put(f"/vendas/{venda_id}", json=update_data)
    assert put_resp.status_code == 200
    venda_atualizada = put_resp.json()
    assert venda_atualizada["quantidade"] == 15
    assert venda_atualizada["preco_unitario"] == 35.0

    # Atualizar com dados inválidos
    invalid_updates = [
        {"quantidade": 0},
        {"preco_unitario": 0},
        {"quantidade": -1},
        {"preco_unitario": -3},
    ]
    for upd in invalid_updates:
        resp = client.put(f"/vendas/{venda_id}", json=upd)
        assert resp.status_code == 422

    # Atualizar venda inexistente
    resp = client.put("/vendas/999", json={"quantidade": 5})
    assert resp.status_code == 404


def test_atualizar_venda_inexistente():
    update_data = {"produto": "Novo Produto"}
    response = client.put("/vendas/999", json=update_data)
    assert response.status_code == 404
