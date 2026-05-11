import subprocess
import sys

def test_hello_world():
    result = subprocess.run([sys.executable, 'output/sistema_gerado.py'], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'Hello, World!'

# Aqui você pode adicionar outros testes para outras funcionalidades conforme necessário.