import sys
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import requests
from bs4 import BeautifulSoup

# Configurações fixas
DB_PATH_DEFAULT = "precos.db"
URL_PRODUTO = "https://www.kabum.com.br/produto/119613/monitor-led-24-samsung-ls24r350fhlxzd-full-hd-hdmi-vga"  # Exemplo público
LOG_PATH = "preco_alerta.log"

# Configuração Logger
logger = logging.getLogger("PrecoAlerta")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# --- Camada Coleta (scraping simples) ---
def get_preco_atual(url: str = URL_PRODUTO) -> Optional[float]:
    """
    Tenta obter o preço atual do produto via scraping.
    Retorna float do preço ou None se falhar.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao acessar URL do produto: {e}")
        return None

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        # Exemplo baseado no Kabum - preço pode estar em tag específica com class "priceCard"
        # Pode ser necessário ajustar caso o site mude.
        # Buscamos conteúdo dentro de span que contenha o preço
        preco_tag = soup.find("span", class_="priceCard")  # Exemplo simples; pode não funcionar sempre
        if not preco_tag:
            # Busca alternativa: span com "priceCard" dentro de div "product-price"
            preco_tag = soup.select_one("div.sc-11uohgb-0 iGmXZy span.priceCard")
        if not preco_tag:
            # Fallback: procurar por qualquer span com "R$"
            spans = soup.find_all("span")
            for sp in spans:
                text = sp.get_text(strip=True)
                if text.startswith("R$"):
                    preco_tag = sp
                    break
        if not preco_tag:
            raise ValueError("Tag com preço não encontrada.")

        texto_preco = preco_tag.get_text().strip()
        # Extrai número do preço, ex: "R$ 1.499,00"
        texto_preco = texto_preco.replace(".", "").replace(",", ".").replace("R$", "").strip()
        preco = float(texto_preco)
        return preco
    except Exception as e:
        logger.error(f"Erro ao extrair preço do HTML: {e}")
        return None


# --- Camada Persistência ---
class BancoPrecos:
    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._criar_tabela_se_necessario()

    def _conn_init(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row

    def _criar_tabela_se_necessario(self) -> None:
        self._conn_init()
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_precos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                preco FLOAT NOT NULL
            )
            """
        )
        self._conn.commit()

    def salvar_preco(self, preco: float) -> None:
        self._conn_init()
        cur = self._conn.cursor()
        agora = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        cur.execute(
            "INSERT INTO historico_precos (timestamp, preco) VALUES (?, ?)",
            (agora, preco),
        )
        self._conn.commit()
        logger.info(f"Preço salvo no banco: R$ {preco:.2f} em {agora}")

    def obter_historico(self) -> List[Dict]:
        self._conn_init()
        cur = self._conn.cursor()
        cur.execute("SELECT id, timestamp, preco FROM historico_precos ORDER BY timestamp DESC")
        rows = cur.fetchall()
        return [{"id": r["id"], "timestamp": r["timestamp"], "preco": r["preco"]} for r in rows]

    def fechar(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# --- Camada Domínio ---
def verificar_alerta(preco: float, limite: float) -> bool:
    """
    Retorna True se o preço está abaixo do limite configurado.
    """
    return preco < limite


# --- Apresentação ---
def gerar_relatorio(historico: List[Dict], alerta_ativo: bool, limite: float) -> None:
    """
    Imprime relatório no terminal com histórico e estado de alerta.
    """
    print("=" * 40)
    print("Relatório de Monitoramento de Preço")
    print(f"Limite de alerta configurado: R$ {limite:.2f}")
    print("- Histórico de preços (mais recente primeiro):")
    if not historico:
        print("  Nenhum dado registrado.")
    else:
        for registro in historico[:10]:
            print(f"  {registro['timestamp']} - R$ {registro['preco']:.2f}")
    print("-" * 40)
    if alerta_ativo:
        alerta_msg = f"ALERTA: Preço está abaixo do limite! Preço atual: R$ {historico[0]['preco']:.2f}"
        print(alerta_msg)
        logger.warning(alerta_msg)
    else:
        print("Nenhum alerta ativo. Preço acima do limite.")
    print("=" * 40)


# --- CLI e Execução principal ---
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sistema de monitoramento de preço com alerta."
    )
    parser.add_argument(
        "--limite",
        type=float,
        default=1500.0,
        help="Limite de preço para disparar alerta (R$). Default=1500.0",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=DB_PATH_DEFAULT,
        help="Caminho do banco SQLite. Default=precos.db",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=URL_PRODUTO,
        help="URL do produto para monitorar",
    )
    args = parser.parse_args(argv)

    logger.info("Iniciando sistema de monitoramento de preço.")
    logger.info(f"Usando limite: R$ {args.limite:.2f}")
    logger.info(f"Banco SQLite: {args.db}")
    logger.info(f"URL produto: {args.url}")

    preco = get_preco_atual(args.url)
    if preco is None:
        logger.error("Não foi possível obter o preço atual do produto.")
        print("Falha ao obter preço do produto. Veja logs para mais detalhes.")
        sys.exit(1)

    banco = BancoPrecos(args.db)
    banco.salvar_preco(preco)

    alerta = verificar_alerta(preco, args.limite)
    if alerta:
        logger.warning(f"Preço {preco:.2f} está abaixo do limite {args.limite:.2f}. ALERTA emitido.")

    historico = banco.obter_historico()
    gerar_relatorio(historico, alerta, args.limite)

    banco.fechar()
    logger.info("Execução finalizada com sucesso.")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Uso básico:")
        print("  python output/sistema_gerado.py --limite 1200.0")
        print("Use --help para ver opções detalhadas.")
        sys.exit(0)
    main()


# Para importar o app no futuro, caso seja API:
# Interface FastAPI não requisitada neste escopo, mas preparado para futuro.
# Expõe main(argv=None) para CLI.