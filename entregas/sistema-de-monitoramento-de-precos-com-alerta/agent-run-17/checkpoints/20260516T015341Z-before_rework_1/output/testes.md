import sys
import subprocess
import os
import sqlite3
import importlib.util
import logging
from pathlib import Path
from unittest import mock
import re

def test_sem_argumentos_mostra_uso():
    # Executa sem argumentos, espera saida do uso basico e codigo 0
    result = subprocess.run(
        [sys.executable, "output/sistema_gerado.py"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Uso basico" in result.stdout


def test_help_argumento():
    # Executa com argumento --help, espera retorno codigo 0 e ajuda no stdout
    result = subprocess.run(
        [sys.executable, "output/sistema_gerado.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Sistema de monitoramento de preco" in result.stdout


def test_preco_atual_valido_e_invalido(monkeypatch):
    # Importa modulo para acessar get_preco_atual
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    # Mock requests.get para retornar HTML com preco valido e incompleto
    class ResponseMock:
        def __init__(self, text, status_code=200):
            self.text = text
            self.status_code = status_code
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception(f"Status code {self.status_code}")

    valid_html = '<span class="priceCard">R$ 1.234,56</span>'
    invalid_html = '<html><head></head><body>No price here</body></html>'

    def mock_get_valid(*args, **kwargs):
        return ResponseMock(valid_html)

    def mock_get_invalid(*args, **kwargs):
        return ResponseMock(invalid_html)

    # Test preco valido
    monkeypatch.setattr(sistema.requests, "get", mock_get_valid)
    preco = sistema.get_preco_atual("http://fakeurl")
    assert preco is not None
    assert isinstance(preco, float)
    assert abs(preco - 1234.56) < 1e-2

    # Test preco invalido (nao encontrado)
    monkeypatch.setattr(sistema.requests, "get", mock_get_invalid)
    preco_none = sistema.get_preco_atual("http://fakeurl")
    assert preco_none is None


def test_salvar_e_obter_historico_em_banco(tmp_path):
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    db_file = tmp_path / "test_precos.db"
    banco = sistema.BancoPrecos(str(db_file))

    # Nenhum dado inicial
    historico_vazio = banco.obter_historico()
    assert historico_vazio == []

    banco.salvar_preco(1000.50)
    banco.salvar_preco(1200.75)

    historico = banco.obter_historico()
    assert len(historico) == 2
    precos = [registro["preco"] for registro in historico]
    assert 1000.50 in precos
    assert 1200.75 in precos

    banco.fechar()


def test_verificar_alerta_limiter():
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    # Preco abaixo do limite: alerta True
    assert sistema.verificar_alerta(1000, 1200) is True
    # Preco igual ao limite: alerta False
    assert sistema.verificar_alerta(1500, 1500) is False
    # Preco acima do limite: alerta False
    assert sistema.verificar_alerta(1600, 1500) is False


def test_fluxo_principal_com_alerta_e_sem_alerta(monkeypatch, tmp_path, capsys):
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    db_file = tmp_path / "test_precos.db"

    # Preco mockado abaixo do limite -> alerta deve ser True
    def mock_get_preco_baixo(url):
        return 1000.0

    # Preco mockado acima do limite -> alerta deve ser False
    def mock_get_preco_alto(url):
        return 2000.0

    monkeypatch.setattr(sistema, "get_preco_atual", mock_get_preco_baixo)
    argv = ["--limite", "1500", "--db", str(db_file), "--url", "http://fakeurl"]
    sistema.main(argv=argv)
    out = capsys.readouterr().out
    assert "ALERTA" in out
    # Verifica que historico tem 1 registro com preco 1000.0
    banco = sistema.BancoPrecos(str(db_file))
    historico = banco.obter_historico()
    banco.fechar()
    assert len(historico) == 1
    assert abs(historico[0]["preco"]-1000.0) < 1e-2

    # Execute novamente com preco acima do limite
    monkeypatch.setattr(sistema, "get_preco_atual", mock_get_preco_alto)
    sistema.main(argv=argv)
    out2 = capsys.readouterr().out
    assert "Nenhum alerta ativo" in out2
    banco = sistema.BancoPrecos(str(db_file))
    historico2 = banco.obter_historico()
    banco.fechar()
    # Agora historico deve ter 2 registros
    assert len(historico2) == 2


def test_falha_coleta_precos(monkeypatch, tmp_path, capsys):
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    def mock_get_preco_none(url):
        return None

    monkeypatch.setattr(sistema, "get_preco_atual", mock_get_preco_none)
    db_file = tmp_path / "test_precos.db"
    argv = ["--limite", "1500", "--db", str(db_file), "--url", "http://fakeurl"]

    with pytest.raises(SystemExit) as excinfo:
        sistema.main(argv=argv)
    out = capsys.readouterr().out
    # Verifica mensagem de falha no output
    assert "Falha ao obter preco" in out
    assert excinfo.value.code == 1


def test_criacao_do_banco_e_conexao(tmp_path):
    spec = importlib.util.spec_from_file_location("sistema_gerado", "output/sistema_gerado.py")
    sistema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sistema)

    db_file = tmp_path / "novo_banco.db"
    assert not db_file.exists()
    banco = sistema.BancoPrecos(str(db_file))
    banco._conn_init()
    # Banco e tabela devem existir
    assert db_file.exists()
    cur = banco._conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_precos'")
    tabela = cur.fetchone()
    assert tabela is not None
    banco.fechar()


# pytest requer import para excecoes e monkeypatch
import pytest