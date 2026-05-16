```markdown
# Sistema de Gestão de Vendas - MVP

Este documento descreve como instalar, configurar, executar, usar e testar o sistema de gestão de vendas desenvolvido com FastAPI e SQLite.

---

## Sumário

- [Descrição do Sistema](#descrição-do-sistema)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Uso da API](#uso-da-api)
- [Testes](#testes)
- [Notas e Considerações](#notas-e-considerações)

---

## Descrição do Sistema

Este é um sistema simples para gerenciamento de vendas, que disponibiliza uma API RESTful com operações CRUD básicas sobre a entidade "Venda". 

- A API foi implementada usando **FastAPI**.
- Os dados são persistidos em um banco **SQLite** local, usando **SQLAlchemy** como ORM.
- A aplicação oferece as seguintes funcionalidades:
  - Criar nova venda.
  - Listar todas as vendas.
  - Consultar uma venda específica pelo ID.
  - Atualizar uma venda existente.
  - Remover uma venda pelo ID.
- Documentação interativa automática da API disponível via Swagger UI.
- Testes unitários cobrindo as principais rotas.

---

## Requisitos

- Python 3.9 ou superior.
- Dependências Python listadas no arquivo `requirements.txt` (criado manualmente ou instalar diretamente conforme abaixo).
- Conexão com rede local para acesso à API, caso use remotamente.

---

## Instalação

Sugere-se criar um ambiente virtual para isolar as dependências:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

Instale as dependências necessárias (supondo que você tenha um `requirements.txt`, caso não, instale manualmente):

```bash
pip install fastapi sqlalchemy uvicorn pydantic pytest
```

> **Observação:** O arquivo `requirements.txt` não é fornecido neste artefato, então a instalação manual diretamente via pip está indicada.

---

## Configuração

- O banco SQLite será criado automaticamente no arquivo `vendas.db` no diretório onde o sistema for executado.
- Nenhuma configuração adicional é necessária para rodar o sistema.
- O arquivo do código-fonte principal é `output/sistema_gerado.py`.

Caso queira alterar o local do banco, isso requer modificação no código para mudar a variável `SISTEMA_DB_PATH`.

---

## Execução

Para executar o sistema e iniciar o servidor FastAPI local na porta padrão 8000, rode o seguinte comando a partir do diretório raiz do projeto:

```bash
python output/sistema_gerado.py --serve
```

- O servidor rodará em `http://127.0.0.1:8000`
- Para parar o servidor, pressione `CTRL+C`.

Caso execute `python output/sistema_gerado.py` sem argumentos, será exibida a instrução simplificada para inicialização.

---

## Uso da API

Após o servidor estar ativo, você pode interagir com a API usando qualquer ferramenta de HTTP (curl, Postman, Insomnia, etc.) ou via documentação automática em:

```
http://127.0.0.1:8000/docs
```

Esta página oferece interface Swagger para visualizar e testar todos os endpoints disponíveis.

### Endpoints disponíveis

| Método | Endpoint       | Descrição                   |
|--------|----------------|-----------------------------|
| POST   | /vendas        | Criar nova venda            |
| GET    | /vendas        | Listar todas as vendas      |
| GET    | /vendas/{id}   | Obter venda por ID          |
| PUT    | /vendas/{id}   | Atualizar dados da venda    |
| DELETE | /vendas/{id}   | Remover venda por ID        |

---

### Formato dos dados de venda

A entidade "Venda" possui os campos JSON abaixo usados em criação e atualização:

| Campo         | Tipo     | Obrigatório | Descrição                  | Observação                   |
|---------------|----------|-------------|----------------------------|------------------------------|
| `item`        | string   | Sim         | Nome do item vendido       |                              |
| `quantidade`  | integer  | Sim         | Quantidade vendida         | Deve ser maior que zero       |
| `valor_unitario` | float  | Sim         | Valor unitário do item     | Deve ser maior que zero       |
| `data_venda`  | string (date-time) | Sim | Data e hora da venda       | Formato ISO 8601 exemplo: `"2023-01-01T10:00:00"` |

Para atualização parcial, os campos são opcionais, mas validam as mesmas regras.

---

### Exemplos práticos de uso

#### Criar uma venda

Request:
```bash
curl -X POST "http://127.0.0.1:8000/vendas" -H "Content-Type: application/json" -d '{
  "item": "Caneta",
  "quantidade": 10,
  "valor_unitario": 2.5,
  "data_venda": "2023-01-01T10:00:00"
}'
```

Response:
```json
{
  "id": 1,
  "item": "Caneta",
  "quantidade": 10,
  "valor_unitario": 2.5,
  "data_venda": "2023-01-01T10:00:00"
}
```

---

#### Listar todas as vendas

Request:
```bash
curl -X GET "http://127.0.0.1:8000/vendas"
```

Response (exemplo):
```json
[
  {
    "id": 1,
    "item": "Caneta",
    "quantidade": 10,
    "valor_unitario": 2.5,
    "data_venda": "2023-01-01T10:00:00"
  }
]
```

---

#### Consultar uma venda pelo ID

Request:
```bash
curl -X GET "http://127.0.0.1:8000/vendas/1"
```

Response:
```json
{
  "id": 1,
  "item": "Caneta",
  "quantidade": 10,
  "valor_unitario": 2.5,
  "data_venda": "2023-01-01T10:00:00"
}
```

Caso a venda não exista, retorna HTTP 404 com:
```json
{"detail":"Venda não encontrada"}
```

---

#### Atualizar uma venda

Request:
```bash
curl -X PUT "http://127.0.0.1:8000/vendas/1" -H "Content-Type: application/json" -d '{
  "quantidade": 15,
  "valor_unitario": 2.3
}'
```

Response:
```json
{
  "id": 1,
  "item": "Caneta",
  "quantidade": 15,
  "valor_unitario": 2.3,
  "data_venda": "2023-01-01T10:00:00"
}
```

---

#### Remover uma venda

Request:
```bash
curl -X DELETE "http://127.0.0.1:8000/vendas/1"
```

Response: HTTP 204 No Content (sem corpo)

Se a venda não existir, retorna HTTP 404.

---

## Testes

Testes unitários foram implementados usando **pytest** e **fastapi.testclient** para validar as operações principais.

### Como rodar os testes

1. Instale o pytest, se ainda não tiver:

```bash
pip install pytest
```

2. Execute os testes (a partir do diretório raiz do projeto):

```bash
pytest
```

Os testes cobrem os seguintes casos:

- Execução do script via CLI sem argumentos e com ajuda.
- Criação de vendas válidas.
- Listagem de vendas (quando vazio e após adição).
- Consulta de venda existente e inexistente.
- Atualização parcial de venda e casos inválidos.
- Remoção de venda existente e tentativa de remover inexistente.
- Validações de campos obrigatórios e valores maiores que zero.

---

## Notas e Considerações

- O sistema não possui autenticação ou controle de acesso.
- Banco SQLite é local e não indicado para alta concorrência ou ambiente produção.
- Documentação interativa da API está disponível automaticamente em `/docs` após iniciar o servidor.
- Para desenvolvimento, pode-se alterar o arquivo `output/sistema_gerado.py` conforme necessidades.

---

## Contato

Para dúvidas ou solicitações de melhoria futuras, favor entrar em contato com o time de desenvolvimento.

---

**Eduarda - Technical Writer**  
Fábrica de Software - Documentação Técnica  
Junho/2024
```