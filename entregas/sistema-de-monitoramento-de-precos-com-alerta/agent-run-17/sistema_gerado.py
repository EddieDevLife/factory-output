import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DATABASE = "precos.db"
DEFAULT_ALERT_LIMIT = 100.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
             " Chrome/58.0.3029.110 Safari/537.3"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI()


class PriceRecord(BaseModel):
    id: int
    product_url: str
    price: float
    timestamp: datetime


class PriceCheckInput(BaseModel):
    url: str = Field(..., description="URL do produto para monitorar")
    alert_limit: Optional[float] = Field(DEFAULT_ALERT_LIMIT, description="Limite de preço para alerta")


def create_table_if_not_exists(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()


def save_price_record(conn: sqlite3.Connection, product_url: str, price: float) -> None:
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO precos (product_url, price, timestamp) VALUES (?, ?, ?)",
        (product_url, price, ts),
    )
    conn.commit()


def fetch_price_from_url(url: str) -> float:
    """
    Faz scraping da página do produto para obter o preço atual.
    Alvo específico para site de e-commerce genérico, tenta extrair preço via BeautifulSoup.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao acessar URL {url}: {str(e)}")
        raise RuntimeError(f"Não foi possível obter o preço atual do produto.") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Tentar encontrar preço no HTML comum para sites e-commerce
    selectors = [
        ".price",  # classe genérica price
        "#priceblock_ourprice",  # exemplo Amazon
        "#priceblock_dealprice",  # exemplo Amazon
        ".a-price-whole",  # Amazon
        ".product-price",  # genérico
        ".valor",  # genérico em pt-br
    ]

    price_text = None
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem and elem.get_text(strip=True):
            price_text = elem.get_text(strip=True)
            break

    if not price_text:
        # fallback: procurar por texto que contenha cifra
        for tag in soup.find_all(string=True):  # corrigido de text=True para string=True
            txt = tag.strip()
            if txt and ("R$" in txt or "$" in txt):
                price_text = txt
                break

    if not price_text:
        logger.error("Não foi possível localizar o preço no HTML da página.")
        raise RuntimeError("Não foi possível obter o preço atual do produto.")

    # Limpar texto e extrair valor float
    import re

    # Retira tudo que não seja números, vírgula, ponto ou dígito
    clean_text = price_text.replace(".", "").replace(",", ".")
    numbers = re.findall(r"\d+\.?\d*", clean_text)
    if not numbers:
        logger.error("Preço extraído inválido: '%s'", price_text)
        raise RuntimeError("Não foi possível interpretar o preço extraído do produto.")

    try:
        price = float(numbers[0])
    except Exception as e:
        logger.error("Erro ao converter preço para float: %s", str(e))
        raise RuntimeError("Falha ao interpretar o preço atual do produto.") from e

    return price


def check_and_alert(price: float, limit: float) -> None:
    if price < limit:
        logger.warning(f"ALERTA: Preço {price:.2f} abaixo do limite {limit:.2f}!")


def monitor_price(product_url: str, alert_limit: float, db_path: Optional[str] = None) -> float:
    if db_path is None:
        db_path = DATABASE
    logger.info("Iniciando monitoramento de preço do produto.")
    price = fetch_price_from_url(product_url)
    logger.info(f"Preço atual do produto: {price:.2f}")

    with sqlite3.connect(db_path) as conn:
        create_table_if_not_exists(conn)
        save_price_record(conn, product_url, price)
        logger.info("Preço salvo no banco de dados com sucesso.")

    check_and_alert(price, alert_limit)

    return price


@app.get("/monitorar-preco", response_model=PriceRecord)
def api_monitorar_preco(url: str, alert_limit: float = DEFAULT_ALERT_LIMIT):
    try:
        price = monitor_price(url, alert_limit)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.utcnow()
    return PriceRecord(id=0, product_url=url, price=price, timestamp=now)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sistema de monitoramento de preço de produto em e-commerce."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL do produto para monitorar",
    )
    parser.add_argument(
        "--alert_limit",
        type=float,
        default=DEFAULT_ALERT_LIMIT,
        help=f"Limite de preço para gerar alerta, default={DEFAULT_ALERT_LIMIT}",
    )

    args = parser.parse_args(argv)

    try:
        price = monitor_price(args.url, args.alert_limit)
    except RuntimeError as e:
        logger.error(f"Falha ao obter preco do produto. Veja logs para mais detalhes.\n{e}")
        sys.exit(1)
    else:
        logger.info(f"Monitoramento concluído. Preço atual: {price:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
