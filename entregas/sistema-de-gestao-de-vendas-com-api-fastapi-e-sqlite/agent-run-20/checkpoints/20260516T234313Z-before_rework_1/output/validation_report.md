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
- PASS - generated_tests_have_meaningful_assertions: 13 testes e 27 asserts significativos encontrados.
- FAIL - generated_tests_pass: Error: module 'sistema_gerado' has no attribute 'Base'
ERROR tests/test_codigo.py::test_remover_venda_inexistente - AttributeError: module 'sistema_gerado' has no attribute 'Base'
ERROR tests/test_codigo.py::test_validacoes_criacao - AttributeError: module 'sistema_gerado' has no attribute 'Base'
ERROR tests/test_codigo.py::test_validacoes_atualizacao - AttributeError: module 'sistema_gerado' has no attribute 'Base'
==================== 1 failed, 1 passed, 11 errors in 1.63s ====================
- PASS - code_style_black: black nao instalado; check de estilo ignorado.
- PASS - type_check_mypy: mypy nao instalado; type check ignorado sem bloquear a entrega.
- PASS - api_tests_use_testclient: Testes de API devem usar TestClient sem servidor externo.
