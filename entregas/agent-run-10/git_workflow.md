# Relatório Operacional de Git/CI para Publicação da Entrega no repositório factory-output

---

## Contexto da entrega

- Repositório destino: https://github.com/EddieDevLife/factory-output
- Branch para entrega: `feat/prioridade-tarefas`
- Artefatos gerados:
  - Código principal da API: `output/sistema_gerado.py`
  - Documentação/README atualizada: `output/README_ATUALIZADO.md`
  - Testes automatizados: `tests/test_codigo.py`

---

## 1. Git: Comandos recomendados para versionamento da entrega

### Passo 1: Clonar o repositório ou atualizar local

```bash
git clone https://github.com/EddieDevLife/factory-output.git
cd factory-output
git checkout main
git pull origin main
```

> Caso já tenha o repositório local: `git checkout main && git pull`

### Passo 2: Criar a branch de feature para entrega

```bash
git checkout -b feat/prioridade-tarefas
```

### Passo 3: Adicionar os artefatos gerados à staging area

```bash
git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py
```

> Verifique se não há arquivos não relacionados incluídos por erro.

### Passo 4: Commit das mudanças com mensagem clara e detalhada

```bash
git commit -m "feat: Implementa API de tarefas com cálculo automático de prioridade

- Código da API em FastAPI com SQLite e SQLModel
- Endpoints para criação, listagem, listagem por prioridade e atualização
- Validações robustas de dados conforme requisitos (impacto, prazo, status)
- Suite de testes completa com pytest e TestClient do FastAPI
- Documentação atualizada com exemplos cURL e instruções de execução

Entrega atende aos critérios do cliente sobre cálculo do Score e ordenação correta das tarefas."
```

### Passo 5: Subir (push) a branch para o repositório remoto

```bash
git push origin feat/prioridade-tarefas
```

---

## 2. Criar Pull Request (PR)

O PR deve ser criado a partir da branch `feat/prioridade-tarefas` para a branch padrão do repositório (geralmente `main`).

### Passos para criação do PR:

- No GitHub, ao abrir a página do repositório, após o push, a interface deve sugerir criar PR.
- Use o título do PR como:

  ```
  feat: Entrega de API de gestão de tarefas com priorização automática
  ```

- Na descrição do PR, inclua:

  - Resumo da funcionalidade entregue.
  - Link para os arquivos principais (ex: paths).
  - Referência aos critérios do cliente e como foram cumpridos.
  - Informações sobre testes automatizados e resultados.

Exemplo de descrição:

```
Entrega da funcionalidade de gerenciamento de tarefas com API FastAPI.

Arquivos principais:
- output/sistema_gerado.py : código da API
- output/README_ATUALIZADO.md : documentação atualizada com exemplos
- tests/test_codigo.py : testes unitários e de integração

Cumprimento dos critérios do cliente:
- Sistema calcula corretamente o Score de prioridade: (Impacto * 2) - (Dias até o prazo)
- API permite criação, atualização e listagem ordenada das tarefas
- Validações rigorosas para impacto, prazo e status
- Testes abrangentes que cobrem os casos de erro e cenário crític

Solicito revisão para aprovação e merge.
```

---

## 3. Critérios de revisão no Pull Request (PR)

Ao revisar o PR, os seguintes critérios devem ser avaliados:

- **Funcionalidade**:
  - API implementa todos os endpoints conforme especificado: POST /tarefas, GET /tarefas, GET /tarefas/prioridade, PUT /tarefas/{id}.
  - Cálculo do Score de prioridade está implementado e testado corretamente.
  - Validação dos dados está coberta e retorna erros apropriados (status 422).
  - Tratamento de erro para atualização de tarefas inexistentes (404).

- **Qualidade do código**:
  - Código legível e organizado.
  - Uso adequado das dependências do FastAPI, Pydantic e SQLModel.
  - Comentários e docstrings quando necessário.

- **Testes automatizados**:
  - Cobertura de testes está adequada, especialmente para o cálculo da prioridade.
  - Testes de integração via TestClient do FastAPI.
  - Testes contemplam casos válidos e inválidos.

- **Documentação**:
  - README atualizado contém instruções claras para instalação, execução e consumo da API.
  - Exemplos cURL claros para os endpoints principais.

- **Git**:
  - Branch correta foi criada.
  - Commit único (pode aceitar mais, mas ideal com commits descritivos se houver).
  - Mensagens de commit claras.

---

## 4. Observações e recomendações para CI/CD

### Recomendações para a pipeline de CI/CD

- **Testes**: Adicionar etapa que execute `pytest` para rodar `tests/test_codigo.py` automaticamente a cada push na branch feat/prioridade-tarefas e no PR.
  
- **Linting e formatação**: Opcionalmente, adicionar ferramentas como `flake8` e `black` para garantir padronização do código.

- **Build e deploy**:

  - Caso haja deploy automático, garantir que o banco de dados SQLite seja tratado corretamente (migrações/tabelas existentes).
  
  - Testar localmente a execução: `python output/sistema_gerado.py --serve` e verificação manual básica.

- **Automação da abertura do PR no CI** (exemplo com GitHub Actions e script):

  - Um workflow pode ser configurado para, após merge em `main`, gerar branch para nova funcionalidade automaticamente e abrir PR com artefato gerado, usando `gh` CLI:

```yaml
name: Delivery Automation

on:
  push:
    branches:
      - main

jobs:
  create-pr:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    - name: Run factory to generate code
      run: |
        python factory_script.py --output output/
    - name: Configure git user
      run: |
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
    - name: Create feature branch
      run: |
        git checkout -b feat/prioridade-tarefas
        git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py
        git commit -m "feat: delivery automática do sistema de tarefas com prioridade"
        git push origin feat/prioridade-tarefas --force
    - name: Create Pull Request
      uses: peter-evans/create-pull-request@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        title: "feat: delivery automática do sistema de tarefas com prioridade"
        body: |
          PR criado automaticamente via workflow de entrega.
        base: main
        head: feat/prioridade-tarefas
```

Este é só um exemplo para um CI que gera o código e cria o PR automaticamente.

---

## 5. Resumo do workflow recomendado manual

```bash
# Clone e preparar branch
git clone https://github.com/EddieDevLife/factory-output.git
cd factory-output
git checkout -b feat/prioridade-tarefas

# Adicionar os arquivos gerados pela fábrica
git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py

# Commit completo e detalhado
git commit -m "feat: Implementa API de tarefas com cálculo automático de prioridade

- Código da API em FastAPI com SQLite e SQLModel
- Endpoints para criação, listagem, listagem por prioridade e atualização
- Validações robustas de dados conforme requisitos (impacto, prazo, status)
- Suite de testes completa com pytest e TestClient do FastAPI
- Documentação atualizada com exemplos cURL e instruções de execução

Entrega atende aos critérios do cliente sobre cálculo do Score e ordenação correta das tarefas."

# Push para o repositório remoto
git push origin feat/prioridade-tarefas
```

Após o push, crie o Pull Request no GitHub a partir da UI para revisão e merge.

---

## 6. Observação final

- O repositório deverá ter no mínimo um workflow para rodar os testes em Push/PR para garantir qualidade antes do merge.
- Documentação deve sempre refletir as últimas atualizações e instruções para reprodução local/produção.
- Caso o cliente deseje, o PR pode incluir links para pipelines e status de testes no corpo do PR.

---

# FIM DO RELATÓRIO OPERACIONAL

Obrigado, estou à disposição para ajudar em integrações ou dúvidas sobre o workflow automatizado e publicação.