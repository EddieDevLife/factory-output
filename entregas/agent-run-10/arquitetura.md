Branch recomendado para entrega: feat/prioridade-tarefas

Esboço da Arquitetura da API (FastAPI):

Modelos de Dados:
- Task
  - id: int (auto-increment)
  - titulo: str
  - descricao: str
  - prazo: date (deadline)
  - impacto: int (1 a 10)
  - status: str (pendente ou concluído)

Rotas API:
- POST /tarefas
  - Criar nova tarefa
  - Validação dos dados: impacto entre 1 e 10, prazo data válida no futuro, status válido

- GET /tarefas
  - Retorna a lista completa de tarefas, podendo opcionalmente filtrar por status
  - Retorna todas as tarefas ordenadas por id (ou data criação, se houver)

- GET /tarefas/prioridade
  - Retorna as tarefas ordenadas pelo Score de Prioridade
  - Score = (Impacto * 2) - (Dias até o Prazo)
  - Calcular a diferença de datas entre hoje e o prazo para o Score
  - Ordenar decrescente pelo Score

- PUT /tarefas/{id}
  - Atualizar tarefa (modificar título, descrição, prazo, impacto, status)
  - Validação igual ao POST

Componentes:
- Camada de Persistência
  - SQLite com SQLAlchemy (ORM) para facilitar a manipulação e validação

- Camada de Serviço/Lógica
  - Função para calcular o Score de prioridade para cada tarefa
  - Função para manipular as tarefas (criar, listar, atualizar)

- Tratamento de erros
  - Tratamento para data inválida (formatos, datas no passado)
  - Validação de impacto e status
  - 404 para tarefa não encontrada ao atualizar

Testes:
- Testes unitários e de integração com pytest
- Validar cálculo do Score corrigido
- Testar endpoints usando TestClient do FastAPI
- Testar cenário crítico: enviar 3 tarefas com prazos e impactos diferentes e verificar ordenação correta

Documentação:
- README.md com instruções de instalação de dependências (FastAPI, Uvicorn, SQLAlchemy, pytest)
- Como rodar a API localmente
- Exemplos de chamadas cURL para:
  - Criar tarefa (POST)
  - Buscar lista de tarefas (GET)
  - Buscar lista ordenada por prioridade (GET /prioridade)
  - Atualizar tarefa (PUT)

---

Este esboço suporta um sistema robusto que cumpre a demanda do cliente, é facilmente testável e flexível para futuros ajustes na fórmula de prioridade ou outros campos.

---

Exemplo de nome da branch para entrega:

```plaintext
feat/prioridade-tarefas
```

---

Agora, o próximo passo será implementar o código conforme desenho acima, com uma estrutura clara e arquivos idênticos a output/sistema_gerado.py para o código principal, além da suíte de testes e README.