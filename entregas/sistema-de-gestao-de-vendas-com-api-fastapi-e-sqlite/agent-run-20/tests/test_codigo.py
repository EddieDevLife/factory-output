import pytest
from fastapi.testclient import TestClient
from fastapi import status
import os
import tempfile
import shutil

# No import sistema_gerado directly to avoid ModuleNotFoundError

# We will dynamically import app and functions after setting DB_PATH
import importlib.util
import sys

module_path = os.path.abspath('output/sistema_gerado.py')
spec = importlib.util.spec_from_file_location('sistema_gerado', module_path)
sg = importlib.util.module_from_spec(spec)
sys.modules['sistema_gerado'] = sg
spec.loader.exec_module(sg)

app = sg.app

# Patch DB_PATH to use a temporary directory to isolate state
@pytest.fixture
def temp_db_path(monkeypatch, tmp_path):
    temp_db = tmp_path / 'test.db'
    monkeypatch.setattr(sg, 'DB_PATH', str(temp_db))
    # Ensure init_db runs on startup uses this path
    sg.init_db()
    yield
    # Cleanup handled by tmp_path

@pytest.fixture

def client(temp_db_path):
    with TestClient(app) as c:
        yield c

# Helper functions for creating clients, products, sales

def create_cliente(client_api, nome='John Doe', email='john@example.com'):
    response = client_api.post('/clientes/', json={'nome': nome, 'email': email})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def create_produto(client_api, nome='Produto X', preco=10.5):
    response = client_api.post('/produtos/', json={'nome': nome, 'preco': preco})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def create_venda(client_api, cliente_id, produto_id, quantidade=1):
    response = client_api.post('/vendas/', json={
        'cliente_id': cliente_id,
        'produto_id': produto_id,
        'quantidade': quantidade
    })
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Testa criação, listagem, obtenção, atualização, deleção de clientes

def test_clientes_crud(client):
    c1 = create_cliente(client, 'Alice', 'alice@example.com')

    # Lista clientes e verifica se Alice está presente
    response = client.get('/clientes/')
    assert response.status_code == status.HTTP_200_OK
    assert any(cli['id'] == c1['id'] for cli in response.json())

    # Obter cliente pelo id
    response = client.get(f"/clientes/{c1['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['nome'] == 'Alice'

    # Atualizar cliente
    response = client.put(f"/clientes/{c1['id']}", json={'nome': 'Alice Updated'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['nome'] == 'Alice Updated'

    # Deletar cliente
    response = client.delete(f"/clientes/{c1['id']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Obter cliente excluído retorna 404
    response = client.get(f"/clientes/{c1['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Testa criação, listagem, obtenção, atualização, deleção de produtos

def test_produtos_crud(client):
    p1 = create_produto(client, 'Produto A', 20.0)

    # Lista produtos e verifica se Produto A está presente
    response = client.get('/produtos/')
    assert response.status_code == status.HTTP_200_OK
    assert any(prod['id'] == p1['id'] for prod in response.json())

    # Obter produto pelo id
    response = client.get(f"/produtos/{p1['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['nome'] == 'Produto A'

    # Atualizar produto
    response = client.put(f"/produtos/{p1['id']}", json={'preco': 25.5})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['preco'] == 25.5

    # Deletar produto
    response = client.delete(f"/produtos/{p1['id']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Obter produto excluído retorna 404
    response = client.get(f"/produtos/{p1['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Testa criação, listagem, obtenção, atualização e deleção de vendas
# também cobre validações de cliente e produto durante venda

def test_vendas_crud(client):
    # Cria cliente e produto para usar na venda
    c = create_cliente(client, 'Cliente Venda', 'venda@example.com')
    p = create_produto(client, 'Produto Venda', 15.0)

    v = create_venda(client, c['id'], p['id'], quantidade=3)

    # Lista vendas e verifica se venda criada está presente
    response = client.get('/vendas/')
    assert response.status_code == status.HTTP_200_OK
    assert any(venda['id'] == v['id'] for venda in response.json())

    # Obter venda pelo id
    response = client.get(f"/vendas/{v['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['quantidade'] == 3

    # Atualizar venda
    c2 = create_cliente(client, 'Outro Cliente', 'outro@example.com')
    p2 = create_produto(client, 'Outro Produto', 30.0)
    response = client.put(
        f"/vendas/{v['id']}",
        json={'cliente_id': c2['id'], 'produto_id': p2['id'], 'quantidade': 5}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['quantidade'] == 5
    assert response.json()['cliente_id'] == c2['id']
    assert response.json()['produto_id'] == p2['id']

    # Deletar venda
    response = client.delete(f"/vendas/{v['id']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Obter venda excluída retorna 404
    response = client.get(f"/vendas/{v['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Testa erro 404 para deletar cliente, produto, venda não existentes

def test_deletar_nao_existentes(client):
    response = client.delete('/clientes/9999')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.delete('/produtos/9999')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.delete('/vendas/9999')
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Testa criação de venda com cliente ou produto inexistente retorna 404

def test_criar_venda_com_erros(client):
    # cliente e produto não existem
    response = client.post('/vendas/', json={'cliente_id': 9999, 'produto_id': 1, 'quantidade': 1})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.post('/vendas/', json={'cliente_id': 1, 'produto_id': 9999, 'quantidade': 1})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # cliente e produto existem, quantidade inválida (0)
    c = create_cliente(client, 'Cliente Teste', 'teste@teste.com')
    p = create_produto(client, 'Produto Teste', 5.0)

    response = client.post('/vendas/', json={'cliente_id': c['id'], 'produto_id': p['id'], 'quantidade': 0})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
