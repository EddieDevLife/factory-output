# API de Gerenciamento de Tarefas com Prioridade

Este é um sistema de API RESTful para gerenciar suas tarefas diárias, com um diferencial importante: cálculo automático de prioridade para ajudá-lo a focar no que realmente importa!

---

## Sumário

- [Visão Geral](#visão-geral)  
- [Instalação](#instalação)  
- [Configuração](#configuração)  
- [Como Rodar o Sistema](#como-rodar-o-sistema)  
- [Endpoints da API](#endpoints-da-api)  
- [Formato dos Dados](#formato-dos-dados)  
- [Exemplos de Uso com cURL](#exemplos-de-uso-com-curl)  
- [Testes Automatizados](#testes-automatizados)  
- [Suporte e Contato](#suporte-e-contato)

---

## Visão Geral

Este sistema foi desenvolvido em **FastAPI** e utiliza o banco de dados **SQLite** para armazenar suas tarefas. Cada tarefa possui as seguintes informações:

- **id**: número único e automático
- **titulo**: nome da tarefa
- **descricao**: detalhamento da tarefa
- **prazo**: data limite para execução (deadline)
- **impacto**: importância da tarefa, valor numérico de 1 a 10
- **status**: `pendente` ou `concluído`

O sistema calcula automaticamente um **Score de Prioridade** para suas tarefas, usando a fórmula:

```plaintext
Score = (Impacto * 2) - (Dias até o Prazo)
```

Ou seja, quanto maior o impacto e mais próximo o prazo, maior a prioridade na lista.

---

## Instalação

1. Clone este repositório ou copie o arquivo principal da API:

```bash
# Exemplo de git clone, adaptável conforme repositório
git clone https://github.com/EddieDevLife/factory-output.git
cd factory-output
```

2. Navegue até a pasta onde o arquivo principal está localizado (`output/sistema_gerado.py`).

3. Crie um ambiente virtual Python (recomendado):

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

4. Instale as dependências necessárias:

```bash
pip install fastapi uvicorn sqlmodel pydantic pytest
```

---

## Configuração

- O sistema utiliza SQLite como banco de dados, que será criado automaticamente no arquivo `tarefas.db` (na mesma pasta do script) ao executar a API pela primeira vez.
- Nenhuma configuração adicional é necessária para uso local.

---

## Como Rodar o Sistema

Para iniciar a API localmente, execute:

```bash
python output/sistema_gerado.py --serve
```

- O servidor será iniciado em `http://127.0.0.1:8000`.
- Uma interface web interativa da documentação da API estará disponível em:  
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Se você rodar o script sem argumentos:

```bash
python output/sistema_gerado.py
```

Você verá uma mensagem com instruções básicas e exemplos de uso.

---

## Endpoints da API

| Método | Rota                | Descrição                               | Detalhes                                                       |
|--------|---------------------|---------------------------------------|----------------------------------------------------------------|
| POST   | `/tarefas`          | Criar uma nova tarefa                  | Valida os dados de entrada e retorna tarefa criada            |
| GET    | `/tarefas`          | Listar todas as tarefas (option filter by status) | Pode filtrar por status (pendente/concluído)<br>Retorna todas ordenadas por id |
| GET    | `/tarefas/prioridade` | Listar tarefas ordenadas por Score de prioridade | O Score é calculado e usado para ordenar as tarefas            |
| PUT    | `/tarefas/{id}`     | Atualizar uma tarefa pelo seu id       | Permite modificar título, descrição, prazo, impacto, status   |

---

## Formato dos Dados

### Tarefa - Dados para criação e leitura

| Campo     | Tipo           | Descrição                          | Restrição                            |
|-----------|----------------|----------------------------------|------------------------------------|
| id        | inteiro        | Identificador único da tarefa    | Auto incrementado (retornado na resposta) |
| titulo    | texto          | Nome da tarefa                   | Obrigatório                        |
| descricao | texto          | Detalhes da tarefa               | Obrigatório                        |
| prazo     | data (YYYY-MM-DD) | Data limite para executar tarefa | Deve ser igual ou posterior a hoje |
| impacto   | inteiro        | Grau de importância (1 a 10)    | Deve estar entre 1 e 10            |
| status    | texto          | Status atual da tarefa           | `pendente` ou `concluído`          |

---

## Exemplos de Uso com cURL

### 1. Criar uma tarefa

```bash
curl -X POST "http://127.0.0.1:8000/tarefas" -H "Content-Type: application/json" -d '{
  "titulo": "Comprar leite",
  "descricao": "Comprar 2 litros de leite no mercado",
  "prazo": "2024-12-31",
  "impacto": 5,
  "status": "pendente"
}'
```

### 2. Listar todas as tarefas

```bash
curl "http://127.0.0.1:8000/tarefas"
```

### 3. Listar tarefas filtrando por status (exemplo: pendente)

```bash
curl "http://127.0.0.1:8000/tarefas?status=pendente"
```

### 4. Listar tarefas ordenadas por prioridade

```bash
curl "http://127.0.0.1:8000/tarefas/prioridade"
```

### 5. Atualizar uma tarefa por ID (exemplo: mudar status para concluído)

```bash
curl -X PUT "http://127.0.0.1:8000/tarefas/1" -H "Content-Type: application/json" -d '{
  "status": "concluído"
}'
```

---

## Testes Automatizados

- O projeto conta com uma suite de testes que valida:
  - Criação de tarefas com dados válidos e inválidos.
  - Cálculo correto do Score de prioridade e ordenação.
  - Atualização e validação dos dados.
  - Respostas e códigos HTTP esperados (ex: 422 para erros de validação, 404 para tarefas não encontradas).
  
- Os testes são escritos com `pytest` e usam o `TestClient` do FastAPI.

- Para executar os testes:

```bash
pytest tests/test_codigo.py
```

---

## Observações Importantes

- O prazo (deadline) deve ser uma data atual ou futura; não são aceitas datas passadas.
- O impacto deve estar entre 1 e 10.
- O status deve ser exatamente "pendente" ou "concluído" (com acento).
- Ao atualizar tarefas, os mesmos critérios de validação são aplicados.
- O sistema cria automaticamente o banco `tarefas.db` na primeira execução, não é necessário criar manualmente.

---

## Suporte e Contato

Caso tenha dúvidas ou precise de ajuda para executar o sistema, sinta-se à vontade para abrir uma issue no repositório ou entrar em contato com a equipe de desenvolvimento.

---

**Obrigado por usar a API de Gerenciamento de Tarefas com Prioridade!**  
Esperamos que ajude você a organizar suas tarefas com mais eficiência.

---

**Local dos arquivos principais:**

- Código-fonte da API: `output/sistema_gerado.py`  
- Banco de dados SQLite gerado: `tarefas.db` (na mesma pasta do script)  

---

# Fim do README atualizado.