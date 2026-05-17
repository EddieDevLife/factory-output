```python
import subprocess
import sys

def test_hello_world():
    result = subprocess.run([sys.executable, 'output/sistema_gerado.py'], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'Hello, World!'

# Aqui você pode adicionar outros testes para outras funcionalidades conforme necessário.
```

[ok] pytest tests/test_codigo.py
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/runner/work/factory-IA/factory-IA/minha-fabrica-agentes
plugins: anyio-4.13.0
collected 1 item

tests/test_codigo.py .                                                   [100%]

============================== 1 passed in 0.02s ===============================