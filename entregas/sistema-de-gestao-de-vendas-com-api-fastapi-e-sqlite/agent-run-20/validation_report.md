# Relatorio de Validacao Automatizada

Status: passed
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
- PASS - generated_tests_have_meaningful_assertions: 5 testes e 35 asserts significativos encontrados.
- PASS - generated_tests_pass: uter.on_event(event_type)  # ty: ignore[deprecated]

tests/test_codigo.py::test_criar_venda_com_erros
  /opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/_pytest/python.py:166: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    result = testfunction(**testargs)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 5 passed, 3 warnings in 0.43s =========================
- PASS - code_style_black: black nao instalado; check de estilo ignorado.
- PASS - type_check_mypy: mypy nao instalado; type check ignorado sem bloquear a entrega.
- PASS - api_tests_use_testclient: Testes de API devem usar TestClient sem servidor externo.
