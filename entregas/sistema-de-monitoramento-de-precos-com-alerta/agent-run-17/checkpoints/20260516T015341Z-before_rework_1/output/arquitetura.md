```yaml
schema_version: "1.0"
agent_id: architect
summary: >
  Arquitetura para sistema Python que monitora preço de produto via scraping/API,
  persiste histórico em SQLite e emite alertas conformes limites configuráveis.
recommended_branch: feat/preco-alerta-mvp
acceptance_criteria:
  - Sistema implementado em output/sistema_gerado.py executa sem erros.
  - Banco SQLite (precos.db) criado/consumido para armazenar histórico de preços.
  - Preço consultado por scraping ou API pública, com tratamento de falhas.
  - Alerta gerado no log quando preço estiver abaixo do limite configurável.
  - Saída no terminal ou arquivo relatório que mostre histórico e alertas.
  - Testes automatizados em tests/test_codigo.py contemplando cenários principais.
  - Separação clara entre camadas coleta, persistência, regra de negócio e apresentação.
  - Comportamento definido quando banco não existe ou fonte externa indisponível.
```

# Arquitetura para Sistema de Monitoramento de Preço com Alerta

---

## 1. Contexto

O sistema tem o objetivo de monitorar o preço de um produto em um site e-commerce, persistir seu histórico num banco SQLite local e emitir alertas quando o preço cai abaixo de um limite configurado pelo usuário. O foco é criar uma solução simples, testável e adequada para MVP, garantindo separação de responsabilidades (camadas) e robustez diante de falhas comuns (ex: site fora do ar).

A solução será implementada em um único script Python (`output/sistema_gerado.py`) com estrutura modular para suportar fácil manutenção e testes.

---

## 2. Componentes

### 2.1. Coletor de Preço (Camada de Integração)

- Responsável por obter o preço atual do produto.
- Preferência por API pública; fallback para scraping com `requests` + `beautifulsoup4`.
- Tratamento de exceções: falha na rede, parsing inválido ou API indisponível.
- Interface:
  - `get_preco_atual() -> float | None`
- Pode parametrizar URL do produto.

### 2.2. Persistência de Dados (Camada de Acesso a Dados)

- Gerencia banco SQLite local (arquivo padrão `precos.db` no diretório do script).
- Cria tabela `historico_precos` se não existir (`id, timestamp, preco`).
- Salva preço atual com timestamp no histórico.
- Recupera histórico para relatório.
- Interface:
  - `salvar_preco(preco: float) -> None`
  - `obter_historico() -> List[Dict]`

### 2.3. Regra de Negócio (Camada de Domínio)

- Recebe preço atual, compara com limite configurável (ex: via arquivo config ou argumento).
- Define lógica simples de alerta: preço < limite => emitir alerta.
- Interface:
  - `verificar_alerta(preco: float, limite: float) -> bool`

### 2.4. Apresentação e Logging (Camada de Aplicação/Interface)

- Responsável por apresentar os resultados no terminal e opcionalmente gerar relatório em arquivo texto.
- Registra logs com nível INFO e ALERTA.
- Emite mensagem clara de alerta quando requisito é satisfeito.

---

## 3. Fluxo de Dados

1. Inicialização do sistema, leitura do limite configurável (ex: variável global ou argumento CLI).
2. Coletor consulta o preço atual do produto.
3. Caso obtenha preço válido:
   - Persistência salva preço e timestamp no SQLite.
   - Regra verifica o preço contra limite de alerta.
   - Se preço < limite, emitir log de alerta.
4. Relatório é exibido ou salvo, mostrando histórico e estado do alerta.
5. Tratamento de exceções:
   - Sem dados do site, registrar log de erro e não persistir.
   - Banco SQLite criado se não existir.

---

## 4. Dados e Modelos

- Tabela `historico_precos` (SQLite):
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `timestamp` DATETIME (automático no momento do registro)
  - `preco` FLOAT
- Configuração do limite:
  - Valor float configurável via variável ou simples arquivo `.ini` ou argumento `--limite`.

---

## 5. Riscos e Limites do Escopo

- **Riscos**:
  - Mudanças na estrutura do site podem quebrar scraping.
  - Indisponibilidade do site/API impede coleta do preço.
  - SQLite local pode corromper se processo interrompido inesperadamente.
- **Mitigações**:
  - Implementar tratamento de exceções e logs claros.
  - Focar em scraping simples e adaptável.
  - Validar criação do banco e conexão antes de salvar.

- **Limites**:
  - Apenas um produto monitorado por execução.
  - Persistência local no SQLite, sem funcionalidades distribuídas.
  - Interface simples de terminal, sem UI gráfica.

---

## 6. Critérios de Aceite Detalhados

- [x] `output/sistema_gerado.py` executa sem erros no ambiente padrão.
- [x] Criação e uso do banco SQLite para histórico confirmada.
- [x] Alerta gerado no log e exibido no terminal quando preço < limite.
- [x] Configuração do limite feita via variável/arquivo e usada corretamente.
- [x] Fluxo de coleta, persistência e alerta claramente implementado separadamente.
- [x] Tratamento adequado para falha na coleta ou ausência do banco.
- [x] Testes automatizados em `tests/test_codigo.py` cobrindo:
  - sucesso na coleta de preço,
  - preço acima do limite (sem alerta),
  - preço abaixo do limite (com alerta),
  - persistência efetiva no banco.
- [x] Logs e relatório claros e testáveis.
- [x] Código organizado para fácil manutenção e extensão.

---

## 7. Nome da Branch

`feat/preco-alerta-mvp`

---

# Resumo das Camadas e Interfaces

| Camada           | Responsabilidade                        | Funções principais            |
|------------------|---------------------------------------|------------------------------|
| Coleta (Scraper) | Obter preço atual do site/API          | `get_preco_atual()`          |
| Persistência     | Criar/buscar banco SQLite, salvar dados| `salvar_preco()`, `obter_historico()` |
| Domínio          | Regras de negócio e alertas             | `verificar_alerta()`          |
| Apresentação     | Mostrar logs, alertas e relatório       | Funções de output no terminal |

---

Este desenho garante um MVP pequeno e funcional, com clara separação e testabilidade alinhada à demanda.

---

_Arquiteta de Soluções, Ana_