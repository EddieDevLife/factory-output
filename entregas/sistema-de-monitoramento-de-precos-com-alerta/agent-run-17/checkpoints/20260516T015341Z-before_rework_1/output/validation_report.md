# Relatorio de Validacao Automatizada

Status: failed
Schema version: 2

## Checks
- PASS - generated_script_exists: Arquivo output/sistema_gerado.py encontrado.
- PASS - python_syntax: Sintaxe Python valida.
- PASS - python_project_py_compile: Todos os arquivos Python compilam com py_compile.
- PASS - generated_module_imports: Modulo gerado importado com sucesso.
- PASS - generated_imports_resolve: Importacoes resolvidas ou declaradas em requirements.
- PASS - generated_has_docstring_or_cli_help: Artefato possui docstring de modulo, docstring em main ou ajuda de CLI.
- PASS - generated_script_has_no_embedded_pytest: Arquivo gerado nao contem testes Pytest embutidos.
- PASS - pydantic_v2_compatible_patterns: Padroes Pydantic 2 compatíveis.
- PASS - update_model_optional_fields_default_none: Campos Optional de modelos Update usam default None.
- PASS - generated_tests_have_meaningful_assertions: 8 testes e 25 asserts significativos encontrados.
- FAIL - generated_tests_pass: b\n  --url URL        URL do produto para monitorar\n', stderr='').stdout
FAILED tests/test_codigo.py::test_falha_coleta_precos - AssertionError: assert 'Falha ao obter preco' in '2026-05-16 01:53:41,522 INFO: Iniciando sistema de monitoramento de preço.\n2026-05-16 01:53:41,524 INFO: Usando limi...OR: Não foi possível obter o preço atual do produto.\nFalha ao obter preço do produto. Veja logs para mais detalhes.\n'
========================= 3 failed, 5 passed in 0.54s ==========================
- PASS - code_style_black: black nao instalado; check de estilo ignorado.
- PASS - type_check_mypy: mypy nao instalado; type check ignorado sem bloquear a entrega.
- FAIL - api_tests_use_testclient: Testes de API devem usar TestClient sem servidor externo.
