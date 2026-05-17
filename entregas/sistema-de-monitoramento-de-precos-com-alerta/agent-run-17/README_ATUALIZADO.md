```markdown
# Sistema de Monitoramento de Preço com Alerta

Este sistema em Python monitora o preço de um produto em um site de e-commerce, registra o histórico dos preços em um banco local SQLite e emite alertas quando o preço cai abaixo de um limite configurável.

---

## Funcionalidades Implementadas

- Consulta o preço atual do produto via scraping simples usando `requests` e `beautifulsoup4`.
- Persiste o histórico de preços em tabela SQLite local (`precos.db` por padrão).
- Permite configurar o limite de preço para o alerta via argumento de linha de comando.
- Emite alerta (log e mensagem no terminal) quando o preço estiver abaixo do limite.
- Gera relatório no terminal com os últimos preços registrados e status do alerta.
- Trata erros na coleta de preço e cria o banco caso não exista.
- Log de informações e alertas gravado em arquivo `preco_alerta.log` e exibido no terminal.
- Possui testes automatizados cobrindo principais cenários em `tests/test_codigo.py`.

---

## Localização do Executável

- Arquivo principal do sistema:  
  ```
  output/sistema_gerado.py
  ```

---

## Requisitos

- Python 3.7 ou superior
- Bibliotecas Python:
  - requests
  - beautifulsoup4

Instale as dependências com:

```bash
pip install -r requirements.txt
```
> *Obs.: Caso não tenha um arquivo `requirements.txt`, instale manualmente:*  
> `pip install requests beautifulsoup4`

---

## Como Executar

Execute o sistema diretamente pela linha de comando:

```bash
python output/sistema_gerado.py --limite VALOR_LIMITE
```

Exemplo:

```bash
python output/sistema_gerado.py --limite 1200.0
```

Parâmetros opcionais:

| Parâmetro    | Descrição                                   | Default                                  |
|--------------|---------------------------------------------|-----------------------------------------|
| `--limite`   | Valor decimal para limite de alerta (R$).  | 1500.0                                  |
| `--db`       | Caminho para o banco SQLite do histórico.  | `precos.db` (na pasta atual)             |
| `--url`      | URL do produto para monitorar o preço.     | URL padrão configurada no script         |

Para ajuda e detalhes:

```bash
python output/sistema_gerado.py --help
```

---

## Funcionamento Interno e Fluxo do Sistema

1. O script inicia e lê os parâmetros passados (limite, banco, URL).
2. Tenta obter o preço atual do produto via scraping.
3. Se o preço for obtido com sucesso:
   - Salva o preço e timestamp no banco SQLite.
   - Verifica se o preço está abaixo do limite configurado.
   - Emite um alerta no log e terminal, caso esteja abaixo do limite.
4. Exibe no terminal um relatório com os últimos preços registrados e estado do alerta.
5. Registra logs no arquivo `preco_alerta.log` para auditoria e análise.

Em caso de falha ao coletar preço, o sistema informa no terminal e termina com código de erro.

---

## Exemplo de Saída no Terminal

```plaintext
========================================
Relatório de Monitoramento de Preço
Limite de alerta configurado: R$ 1200.00
- Histórico de preços (mais recente primeiro):
  2024-06-05 15:32:10 - R$ 1.100.00
  2024-06-04 15:32:00 - R$ 1.250.00
----------------------------------------
ALERTA: Preço está abaixo do limite! Preço atual: R$ 1100.00
========================================
```

---

## Logs

- Os logs são exibidos no terminal e também gravados no arquivo:

```
preco_alerta.log
```

- Níveis de logs disponíveis:
  - INFO: Informações gerais do processo (início, salvamento, finalização).
  - ERROR: Falhas ao acessar URL ou extrair preço.
  - WARNING: Alertas de preço abaixo do limite.

---

## Estrutura de Dados

- Banco SQLite (`precos.db` por padrão) contém tabela:

| Campo    | Tipo                  | Descrição                      |
|----------|-----------------------|--------------------------------|
| id       | INTEGER (PK autoinc.) | Identificador do registro       |
| timestamp| DATETIME              | Data e hora do registro         |
| preco    | FLOAT                 | Valor do preço capturado        |

---

## Testes Automatizados

Os testes estão localizados em:

```
tests/test_codigo.py
```

Eles abrangem os seguintes cenários:

- Execução sem argumentos mostrando mensagem de uso.
- Teste da opção `--help`.
- Coleta de preço:
  - Sucesso na obtenção de preço válido.
  - Falha ao obter preço (HTML sem valor válido).
- Salvamento e recuperação de histórico no banco SQLite.
- Verificação correta do alerta baseado em limite configurado.
- Fluxo principal testado com preço abaixo e acima do limite.
- Comportamento quando não consegue obter preço (saída com erro).
- Criação e existência da tabela no banco.

Para executar os testes use:

```bash
pytest tests/test_codigo.py
```

Ou, se preferir executar todos os testes da pasta:

```bash
pytest tests/
```

---

## Logs para Depuração

Para acompanhar o fluxo detalhado em execução, consulte o arquivo `preco_alerta.log` gerado na pasta onde o script foi executado.

---

## Observações e Limitações

- O scraping é simples e baseado em uma estrutura HTML do site Kabum; mudanças no site podem exigir ajustes no código.
- O sistema atualmente monitora apenas um produto por execução.
- Banco SQLite é local e não suporta acesso concorrente intenso.
- Interface de linha de comando apenas, sem interface gráfica.
- Caso a coleta de preço falhe, o sistema aborta a execução com mensagem clara e logs de erro.

---

## Contato e Suporte

Para dúvidas ou melhorias, entre em contato com a equipe técnica da fábrica.

---

## Licença

Este sistema é entregue como MVP para avaliação da funcionalidade de monitoramento com alertas.

---

*Documentação gerada por Eduarda, Technical Writer da fábrica.*

```