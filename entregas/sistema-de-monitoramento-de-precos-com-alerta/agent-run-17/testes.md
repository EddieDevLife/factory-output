import pytest
import sqlite3
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from output import sistema_gerado as sg

client = TestClient(sg.app)

# Helper to create in-memory DB and run persistence tests

@patch('output.sistema_gerado.requests.get')
def test_fetch_price_from_url_success(mock_get):
    # Prepare a fake html with a price
    html = '<html><body><span class="price">R$ 123,45</span></body></html>'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_get.return_value = mock_resp

    price = sg.fetch_price_from_url('http://fake-url.com/product')
    assert isinstance(price, float)
    assert price == 123.45


@patch('output.sistema_gerado.requests.get')
def test_fetch_price_from_url_fail_no_price(mock_get):
    html = '<html><body><p>No price here</p></body></html>'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_get.return_value = mock_resp

    with pytest.raises(RuntimeError) as excinfo:
        sg.fetch_price_from_url('http://fake-url.com/product')
    assert 'Não foi possível obter o preço atual do produto.' in str(excinfo.value)


@patch('output.sistema_gerado.requests.get')
def test_monitor_price_and_persistence(mock_get, tmp_path):
    html = '<html><body><span class="price">R$ 50,00</span></body></html>'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html
    mock_get.return_value = mock_resp

    db_file = tmp_path / "test_precos.db"

    price = sg.monitor_price('http://fake-url.com/product', 100, db_path=str(db_file))
    assert price == 50.0

    # Check saved price in DB
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT product_url, price FROM precos")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'http://fake-url.com/product'
    assert row[1] == 50.0


def test_check_and_alert_logs(caplog):
    caplog.set_level(logging.WARNING)
    sg.check_and_alert(49.99, 50.00)
    assert any("ALERTA" in message for message in caplog.messages)

    caplog.clear()
    sg.check_and_alert(50.01, 50.00)
    assert not any("ALERTA" in message for message in caplog.messages)


def test_api_monitorar_preco_success():
    with patch('output.sistema_gerado.monitor_price') as mock_monitor:
        mock_monitor.return_value = 99.99
        response = client.get('/monitorar-preco?url=http://fake-url.com/product&alert_limit=100')
        assert response.status_code == 200
        data = response.json()
        assert data['price'] == 99.99
        assert data['product_url'] == 'http://fake-url.com/product'


def test_api_monitorar_preco_runtime_error():
    with patch('output.sistema_gerado.monitor_price') as mock_monitor:
        mock_monitor.side_effect = RuntimeError('Erro monitoramento')
        response = client.get('/monitorar-preco?url=http://fake-url.com/product&alert_limit=100')
        assert response.status_code == 400
        data = response.json()
        assert 'Erro monitoramento' in data['detail']


@patch('output.sistema_gerado.fetch_price_from_url')
def test_main_success(mock_fetch):
    mock_fetch.return_value = 45.0
    result = sg.main(['--url', 'http://fake-url.com/product', '--alert_limit', '50'])
    assert result == 0


@patch('output.sistema_gerado.fetch_price_from_url')
def test_main_fail(mock_fetch):
    mock_fetch.side_effect = RuntimeError('Falha')
    with patch('sys.exit') as mock_exit:
        sg.main(['--url', 'http://fake-url.com/product', '--alert_limit', '50'])
        mock_exit.assert_called_with(1)


# Added tests for alert triggering conditions
@patch('output.sistema_gerado.fetch_price_from_url')
def test_monitor_price_alert_below_limit(mock_fetch):
    mock_fetch.return_value = 49.0
    with patch('output.sistema_gerado.logger.warning') as mock_warning:
        price = sg.monitor_price('http://fake-url.com/product', 50.0)
        assert price == 49.0
        mock_warning.assert_called_with("ALERTA: Preço 49.00 abaixo do limite 50.00!")


@patch('output.sistema_gerado.fetch_price_from_url')
def test_monitor_price_no_alert_above_limit(mock_fetch):
    mock_fetch.return_value = 51.0
    with patch('output.sistema_gerado.logger.warning') as mock_warning:
        price = sg.monitor_price('http://fake-url.com/product', 50.0)
        assert price == 51.0
        mock_warning.assert_not_called()


# Ensure API uses TestClient and no external server
# Checked by use of TestClient here