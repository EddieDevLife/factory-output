```markdown
# Relatório Operacional de CI/CD e Publicação
## Projeto: Sistema de Gestão de Vendas (MVP) com FastAPI + SQLite
### Repositório: https://github.com/EddieDevLife/factory-output

---

# 1. Branching e Versionamento


| Passo           | Comando Git Exemplo                                      | Detalhes                                                                             |
|-----------------|---------------------------------------------------------|--------------------------------------------------------------------------------------|
| Criar branch    | `git checkout -b sales-mgmt-fastapi-sqlite`             | Branch baseada na recomendação do arquiteto, isolando a entrega do MVP de sistema.   |
| Adicionar arquivos | `git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py` | Artefatos reais gerados pela fábrica.                                               |
| Commit          | `git commit -m "feat: entrega do MVP Sistema Gestão de Vendas com API FastAPI e SQLite"` | Mensagem clara e padronizada para identificar a finalidade do commit.               |
| Push            | `git push origin sales-mgmt-fastapi-sqlite`             | Subir o branch para o repositório remoto.                                           |
| Abrir Pull Request | Via interface GitHub ou CLI (ex. `gh pr create -B main -H sales-mgmt-fastapi-sqlite -t "Entrega MVP Sistema Gestão de Vendas" -b "Descrição da entrega"`) | Base no main principal; branch de origem sales-mgmt-fastapi-sqlite.                  |

---

# 2. Validação Pré-Push (pre-push hook)

Para garantir qualidade antes do push, configure um hook git `pre-push` que rode o CI localmente, validando:

- Execução dos testes unitários (`pytest`)
- Análise estática básica (ex: flake8, mypy - se aplicável)
- Validação de formato de commit (ex: commitlint)

Exemplo simplificado de comando no `pre-push`:

```bash
pytest tests/test_codigo.py && echo 'Tests passed' || { echo 'Tests failed'; exit 1; }
```

> **Passo crítico:** Esse hook garante que somente código com testes verdes vai para o repositório remoto, reduzindo erros posteriores.

---

# 3. Pull Request (PR)

- **Origem:** branch `sales-mgmt-fastapi-sqlite`
- **Destino:** branch `main`
- **Título:** `Entrega MVP Sistema Gestão de Vendas com FastAPI e SQLite`
- **Descrição:**
  - Contém código funcional para CRUD da entidade Venda.
  - Persistência local usando SQLite.
  - Testes automatizados para endpoints principais.
  - Documentação mínima atualizada (README_ATUALIZADO.md).
  - Artefatos localizados em:
    - Código: `output/sistema_gerado.py`
    - Documentação: `output/README_ATUALIZADO.md`
    - Testes: `tests/test_codigo.py`

### Critérios para revisão humana do PR

- Revisão de código focada em:
  - Conformidade com requisitos iniciais de API e banco.
  - Cobertura dos testes unitários para rotas CRUD.
  - Boas práticas de código Python e FastAPI.
  - Observância de padrões da fábrica quanto à estrutura.
- Revisão da documentação para clareza e completude.
- Verificação se os testes passam na pipeline CI.

> **Observação:** A aprovação humana é obrigatória antes da mesclagem.

---

# 4. Integração Contínua (CI)

Recomenda-se pipeline CI declarada em `.github/workflows/ci.yml` ou outra plataforma adotada, executando, automaticamente, após push em branches de feature e PR:

- Instalar dependências (FastAPI, SQLAlchemy, pytest, etc.)
- Executar linters e validadores de código.
- Rodar testes unitários presentes em `tests/test_codigo.py`.
- Gerar relatório de cobertura (opcional).
- Reportar falhas bloqueantes para validadores e testes.

Exemplo resumido do fluxo CI:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install fastapi sqlalchemy uvicorn pytest
      - name: Run tests
        run: pytest tests/test_codigo.py
```

---

# 5. Workflow Automatizado para Criação do PR

- Desenvolvedor cria branch local com nome correto, realiza commits e push.
- Integração com plataforma GitHub pode usar **GitHub Actions** ou outro bot para:
  - Validar push no repositório.
  - Se configurado, gerar PR automático via API GitHub, por exemplo:

```bash
gh pr create --base main --head sales-mgmt-fastapi-sqlite --title "Entrega MVP Sistema Gestão de Vendas" --body "Entrega automatizada via CI/CD."
```

- A equipe recebe notificação para iniciar revisão humana.

---

# 6. Critérios de Rollback

- Caso bugs sejam detectados pós-merge em produção:

  1. Abrir uma nova branch baseada na `main` corrigida, ex: `hotfix/sale-api-bugfix`
  2. Implementar correções necessárias.
  3. Realizar testes locais e validar com pipeline CI.
  4. Abrir novo PR para main e solicitar revisão.
  5. Caso a correção seja emergencial, realizar revert do merge PR original:

     ```bash
     git revert -m 1 <commit_hash_merge_pr>
     git push origin main
     ```

  6. Acionar rollback automático no ambiente de produção caso integrado (dependente da infraestrutura, não contemplado aqui explicitamente).

- Manter o histórico do rollback bem documentado em mensagens de commit para rastreabilidade.

---

# 7. Observações e Recomendações Finais

- **Validação humana obrigatória:** Cada PR deve passar por revisão manual antes do merge, validando lógica, cobertura e clareza da documentação.
- **Bases reais da fábrica:** Uso exclusivo dos artefatos gerados `output/sistema_gerado.py`, `output/README_ATUALIZADO.md` e `tests/test_codigo.py` para garantir rastreabilidade e autenticidade.
- **Não modificar arquivos fora do escopo além de README atualizado e testes.**
- **Manutenção do ambiente local SQLite:** Verificar permissão para banco `vendas.db` e documentar alertas para ambientes concorrentes.
- **Para deploy, pipeline adicional deve ser configurado conforme ambiente (não detalhado aqui).**

---

# 8. Resumo dos Comandos Git Recomendados

```bash
# Criar e acessar a branch da entrega
git checkout -b sales-mgmt-fastapi-sqlite

# Adicionar arquivos da entrega
git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py

# Commitar alterações
git commit -m "feat: entrega do MVP Sistema Gestão de Vendas com API FastAPI e SQLite"

# Validar localmente com testes (pré-push)
pytest tests/test_codigo.py

# Push da branch para remoto
git push origin sales-mgmt-fastapi-sqlite

# Criar PR (usando GitHub CLI)
gh pr create -B main -H sales-mgmt-fastapi-sqlite -t "Entrega MVP Sistema Gestão de Vendas" -b "Entrega validada gerada pela fábrica de software."
```

---

Este relatório cobre o fluxo completo para versionamento seguro, CI/CD com validação e revisão humana, PR e rollback com uso dos artefatos oficiais da fábrica.

---

**Daniel - Engenheiro DevOps**  
Fábrica de Software - Junho/2024
```
