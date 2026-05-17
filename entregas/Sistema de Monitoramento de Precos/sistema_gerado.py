import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


DATABASE = "data/precos.db"
DEFAULT_ALERT_LIMIT = 100.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
             " Chrome/58.0.3029.110 Safari/537.3"
ALLOWED_HOSTS = {"www.drogariasaopaulo.com.br", "drogariasaopaulo.com.br"}


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

class MonitorResult(BaseModel):
    product_url: str
    price: float
    alert_limit: float
    below_limit: bool
    timestamp: datetime


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
    Nesta versão, o monitoramento é suportado apenas para Drogaria São Paulo.
    """
    host = urlparse(url).netloc.lower()
    if host not in ALLOWED_HOSTS:
        raise RuntimeError(
            "URL não suportada. Este monitoramento está habilitado apenas para a Drogaria São Paulo."
        )

    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao acessar URL {url}: {str(e)}")
        raise RuntimeError(f"Não foi possível obter o preço atual do produto.") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Drogaria SP (VTEX): a forma mais estável costuma ser `meta[itemprop="price"]`
    meta_price = soup.find("meta", attrs={"itemprop": "price"})
    price_text = (meta_price.get("content") if meta_price else None) or None

    if not price_text:
        # fallback: alguns layouts podem expor meta de OpenGraph/FB
        meta_og = soup.find("meta", attrs={"property": "product:price:amount"}) or soup.find(
            "meta", attrs={"property": "og:price:amount"}
        )
        price_text = (meta_og.get("content") if meta_og else None) or None

    if not price_text:
        logger.error("Não foi possível localizar o preço no HTML da página.")
        raise RuntimeError("Não foi possível obter o preço atual do produto.")

    # Tentar interpretar direto (meta price geralmente já é numérico)
    direct = price_text.strip().replace("R$", "").strip().replace(",", ".")
    try:
        return float(direct)
    except Exception:
        pass

    # Fallback: limpar texto e extrair valor float
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


def get_db_path(db_path: Optional[str] = None) -> str:
    path = db_path or DATABASE
    # Garante que o diretório exista se o usuário passar algo como "data/precos.db"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


@app.get("/monitorar-preco", response_model=MonitorResult)
def api_monitorar_preco(url: str, alert_limit: float = DEFAULT_ALERT_LIMIT, db: Optional[str] = None):
    try:
        db_path = get_db_path(db)
        price = monitor_price(url, alert_limit, db_path=db_path)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.utcnow()
    return MonitorResult(
        product_url=url,
        price=price,
        alert_limit=alert_limit,
        below_limit=price < alert_limit,
        timestamp=now,
    )


@app.get("/historico", response_model=list[PriceRecord])
def api_historico(limit: int = 50, url: Optional[str] = None, db: Optional[str] = None):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit deve estar entre 1 e 500")

    db_path = get_db_path(db)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        create_table_if_not_exists(conn)
        cur = conn.cursor()
        if url:
            cur.execute(
                "SELECT id, product_url, price, timestamp FROM precos WHERE product_url = ? ORDER BY id DESC LIMIT ?",
                (url, limit),
            )
        else:
            cur.execute(
                "SELECT id, product_url, price, timestamp FROM precos ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()

    out: list[PriceRecord] = []
    for r in rows:
        out.append(
            PriceRecord(
                id=int(r["id"]),
                product_url=str(r["product_url"]),
                price=float(r["price"]),
                timestamp=datetime.fromisoformat(str(r["timestamp"])),
            )
        )
    return out


@app.get("/dashboard", include_in_schema=False)
def api_dashboard() -> HTMLResponse:
    html_path = Path(__file__).parent / "web" / "dashboard.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


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
