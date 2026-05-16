```markdown
# Relatório Operacional de CI/CD e Publicação  
Sistema de Monitoramento de Preço com Alerta - Versão MVP

---

## Branch de trabalho recomendada
```bash
git checkout -b feat/preco-alerta-mvp
```

---

## Comandos Git para versionamento da entrega

### 1. Criar branch
```bash
git checkout -b feat/preco-alerta-mvp
```

### 2. Adicionar artefatos reais gerados pela fábrica
```bash
git add output/sistema_gerado.py output/README_ATUALIZADO.md tests/test_codigo.py
```

### 3. Commit
```bash
git commit -m "feat: implementa sistema monitoramento preco com alerta, persistencia SQLite e testes"
```

### 4. Push para remote (origin)
```bash
git push -u origin feat/preco-alerta-mvp
```

---

## Abertura de Pull Request (PR) via GitHub CLI (ou manual)

### Utilizando GitHub CLI para automatizar abertura de PR
```bash
gh pr create --base main --head feat/preco-alerta-mvp --title "feat(preco-alerta): implementação MVP monitoramento preco" --body "Entrega do sistema Python que monitora preço com alerta, banco SQLite e testes. \n\n Inclui os arquivos:\n- output/sistema_gerado.py\n- output/README_ATUALIZADO.md\n- tests/test_codigo.py\n\nPeço revisão para validação dos critérios técnicos e testes."
```

> **Nota**: O passo da revisão humana é obrigatório antes de mesclar a branch.

---

## Fluxo CI/CD recomendado para pull request

1. **Validação automática (CI) ao abrir PR:**
    - Instalação do ambiente Python.
    - Instalação das dependências requeridas (requests, beautifulsoup4, pytest).
    - Execução dos testes automáticos `pytest tests/test_codigo.py`.
    - Verificação da execução do script principal com mock de coleta (ex: teste sem realizar scraping real para garantir não quebra).
    - Checagem de formatação de código (ex: `flake8` ou `black` para padrão consistente).
    - Reportar falhas imediatamente para o autor do PR.

2. **Critérios de revisão do PR:**
    - **Revisão humana obrigatória** para:
      - Garantir que o código em `output/sistema_gerado.py` segue padrão estabelecido de separação de camadas.
      - Validar que a documentação em `output/README_ATUALIZADO.md` está clara e precisa.
      - Confirmar testes automáticos cobrem adequadamente os cenários solicitados.
      - Assegurar mensagens de commit e PR claras para histórico.
      - Confirmar uso verdadeiro do banco de dados SQLite local, e que não há informações sensíveis ou desnecessárias versionadas.
      - Checar logs e tratamento de erros para robustez.

3. **Merge e deploy:**
    - Após aprovação, mesclar PR na branch `main`.
    - Opcionalmente disparar pipeline de build/deploy se houver etapa downstream (extrair relatórios, integrá-los em sistemas de alerta, etc).
    - Garantir que rollback manual esteja documentado.

---

## Critérios para Rollback

Em caso de necessidade de reversão após merge/implantação, seguir operações:

1. Identificar commit anterior seguro em `main`:
```bash
git log main --oneline
```
2. Reverter merge ou reset para commit anterior:
```bash
git revert <commit_hash_merge_pr>
# ou para reset (se for ambiente local e permitir)
git reset --hard <commit_hash_estavel>
git push origin main --force
```
3. Avisar time, documentar incidente e registrar lições aprendidas.

> **Importante:** Rollback envolve operação com potencial impacto, sempre executar com cuidado e em ambiente controlado.

---

## Observações importantes

- O workflow automatizado depende da revisão humana para garantir a qualidade do código e aderência ao contrato.
- Todo push deve ser feito para branch isolada de feature (`feat/preco-alerta-mvp`).
- PRs abertos geram pipeline CI que impede merges com falhas nos testes.
- Os artefatos versionados são exclusivamente:
  - `output/sistema_gerado.py`: código principal gerado pela fábrica.
  - `output/README_ATUALIZADO.md`: documentação atualizada da solução.
  - `tests/test_codigo.py`: testes automáticos cobrindo os cenários principais.
- Nenhum artefato binário ou temporário deve ser versionado neste fluxo.
- Logs gerados em execução são locais e não versionados.
- Configurações sensíveis (ex: URL com token privado) devem ser gerenciadas fora do repositório.

---

## Resumo das etapas operacionais

| Etapa               | Comando/Ferramenta                                 | Dependência Revisão Humana? |
|---------------------|----------------------------------------------------|-----------------------------|
| Criar branch         | `git checkout -b feat/preco-alerta-mvp`           | Não                         |
| Adicionar e commitar | `git add` + `git commit -m`                        | Não                         |
| Push da branch      | `git push -u origin feat/preco-alerta-mvp`         | Não                         |
| Abrir PR             | `gh pr create` ou abrir manual no GitHub           | Não                         |
| Validar CI           | Pipeline automatizada executa testes e lint         | Não (executado automaticamente) |
| Revisar PR           | Revisão humana da equipe                             | **Sim, obrigatória**          |
| Mesclar PR           | Merge no `main` após aprovação                       | Depende da revisão           |
| Rollback se necessário| `git revert` ou `git reset`                         | Sim, decisão humana          |

---

## Contato para dúvidas

Engenheiro DevOps responsável: **Daniel**  
Email: daniel.devops@fabrica.com.br  
Slack #devops-fabrica

---

# Encerramento

Este documento formaliza os procedimentos Git/CICD para gerenciar o versionamento e publicação segura da solução de monitoramento de preços gerada pela fábrica.

Qualquer alteração no processo deve ser discutida e validada pelo time DevOps e equipe de engenharia da fábrica.

---

*Relatório gerado por Daniel - Engenheiro DevOps Especialista*  
*Data: 2024-06-05*  
```