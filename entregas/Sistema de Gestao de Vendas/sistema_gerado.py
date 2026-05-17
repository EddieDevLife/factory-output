"""
Módulo sistema_gerado.py

Sistema de Gestão de Vendas com API FastAPI e SQLite

Este módulo expõe a aplicação FastAPI como `app` e uma interface de linha de comando `main(argv=None)`.

Uso:
    python output/sistema_gerado.py         # Executa CLI com código de saída 0
    python output/sistema_gerado.py --help # Mostrar ajuda CLI
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional, List
from argparse import ArgumentParser

from fastapi import FastAPI, HTTPException
from fastapi import Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from sqlite3 import connect, Connection, Row


# --- Banco de dados ---

# Usa caminho absoluto relativo a este arquivo para evitar depender do CWD.
DB_PATH = str((Path(__file__).parent / "output" / "sistema_gerado.db").resolve())


def get_connection() -> Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(DB_PATH)
    conn.row_factory = Row
    return conn


def init_db() -> None:
    """Inicializa o banco de dados criando as tabelas necessárias."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL CHECK(preco >= 0)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL CHECK(quantidade > 0),
                FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                FOREIGN KEY(produto_id) REFERENCES produtos(id)
            )
            """
        )
        conn.commit()


# --- Modelos Pydantic ---

class Cliente(BaseModel):
    id: Optional[int] = None
    nome: str
    email: str


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None


class Produto(BaseModel):
    id: Optional[int] = None
    nome: str
    preco: float = Field(..., ge=0)


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    preco: Optional[float] = Field(None, ge=0)


class Venda(BaseModel):
    id: Optional[int] = None
    cliente_id: int
    produto_id: int
    quantidade: int = Field(..., gt=0)


class VendaUpdate(BaseModel):
    cliente_id: Optional[int] = None
    produto_id: Optional[int] = None
    quantidade: Optional[int] = Field(None, gt=0)


# --- CRUD internos do BD ---


def criar_cliente(cliente: Cliente) -> Cliente:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, email) VALUES (?, ?)",
            (cliente.nome, cliente.email),
        )
        cliente_id = cursor.lastrowid
        conn.commit()
    return Cliente(id=cliente_id, nome=cliente.nome, email=cliente.email)


def listar_clientes() -> List[Cliente]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email FROM clientes")
        rows = cursor.fetchall()
    return [Cliente(id=row["id"], nome=row["nome"], email=row["email"]) for row in rows]


def obter_cliente(cliente_id: int) -> Cliente:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, email FROM clientes WHERE id = ?", (cliente_id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return Cliente(id=row["id"], nome=row["nome"], email=row["email"])


def atualizar_cliente(cliente_id: int, atualizacao: ClienteUpdate) -> Cliente:
    cliente_existente = obter_cliente(cliente_id)
    nome = atualizacao.nome if atualizacao.nome is not None else cliente_existente.nome
    email = atualizacao.email if atualizacao.email is not None else cliente_existente.email

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clientes SET nome = ?, email = ? WHERE id = ?", (nome, email, cliente_id)
        )
        conn.commit()
    return Cliente(id=cliente_id, nome=nome, email=email)


def deletar_cliente(cliente_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        conn.commit()


def criar_produto(produto: Produto) -> Produto:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, preco) VALUES (?, ?)",
            (produto.nome, produto.preco),
        )
        produto_id = cursor.lastrowid
        conn.commit()
    return Produto(id=produto_id, nome=produto.nome, preco=produto.preco)


def listar_produtos() -> List[Produto]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco FROM produtos")
        rows = cursor.fetchall()
    return [Produto(id=row["id"], nome=row["nome"], preco=row["preco"]) for row in rows]


def obter_produto(produto_id: int) -> Produto:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
    return Produto(id=row["id"], nome=row["nome"], preco=row["preco"])


def atualizar_produto(produto_id: int, atualizacao: ProdutoUpdate) -> Produto:
    produto_existente = obter_produto(produto_id)
    nome = atualizacao.nome if atualizacao.nome is not None else produto_existente.nome
    preco = atualizacao.preco if atualizacao.preco is not None else produto_existente.preco

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE produtos SET nome = ?, preco = ? WHERE id = ?", (nome, preco, produto_id)
        )
        conn.commit()
    return Produto(id=produto_id, nome=nome, preco=preco)


def deletar_produto(produto_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        conn.commit()


def criar_venda(venda: Venda) -> Venda:
    # Validar cliente e produto existentes
    obter_cliente(venda.cliente_id)
    obter_produto(venda.produto_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vendas (cliente_id, produto_id, quantidade) VALUES (?, ?, ?)",
            (venda.cliente_id, venda.produto_id, venda.quantidade),
        )
        venda_id = cursor.lastrowid
        conn.commit()
    return Venda(id=venda_id, cliente_id=venda.cliente_id, produto_id=venda.produto_id, quantidade=venda.quantidade)


def listar_vendas() -> List[Venda]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, cliente_id, produto_id, quantidade FROM vendas")
        rows = cursor.fetchall()
    return [
        Venda(
            id=row["id"],
            cliente_id=row["cliente_id"],
            produto_id=row["produto_id"],
            quantidade=row["quantidade"],
        )
        for row in rows
    ]


def obter_venda(venda_id: int) -> Venda:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, cliente_id, produto_id, quantidade FROM vendas WHERE id = ?",
            (venda_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
    return Venda(
        id=row["id"],
        cliente_id=row["cliente_id"],
        produto_id=row["produto_id"],
        quantidade=row["quantidade"],
    )


def atualizar_venda(venda_id: int, atualizacao: VendaUpdate) -> Venda:
    venda_existente = obter_venda(venda_id)

    cliente_id = (
        atualizacao.cliente_id
        if atualizacao.cliente_id is not None
        else venda_existente.cliente_id
    )
    produto_id = (
        atualizacao.produto_id
        if atualizacao.produto_id is not None
        else venda_existente.produto_id
    )
    quantidade = (
        atualizacao.quantidade
        if atualizacao.quantidade is not None
        else venda_existente.quantidade
    )

    # Validar cliente e produto
    obter_cliente(cliente_id)
    obter_produto(produto_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vendas SET cliente_id = ?, produto_id = ?, quantidade = ? WHERE id = ?",
            (cliente_id, produto_id, quantidade, venda_id),
        )
        conn.commit()

    return Venda(id=venda_id, cliente_id=cliente_id, produto_id=produto_id, quantidade=quantidade)


def deletar_venda(venda_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        conn.commit()


# --- FastAPI app ---

app = FastAPI(title="Sistema de Gestão de Vendas")


@app.on_event("startup")
def startup_event() -> None:
    init_db()

@app.get("/tester", include_in_schema=False)
def api_tester() -> HTMLResponse:
    """
    Página HTML para testar as APIs diretamente no browser.
    Servir pelo mesmo host/porta evita problemas de CORS (vs abrir file://).
    """
    html_path = Path(__file__).parent / "web" / "api_tester.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# Clientes

@app.post("/clientes/", response_model=Cliente, status_code=201)
def api_criar_cliente(cliente: Cliente) -> Cliente:
    return criar_cliente(cliente)


@app.get("/clientes/", response_model=List[Cliente])
def api_listar_clientes() -> List[Cliente]:
    return listar_clientes()


@app.get("/clientes/{cliente_id}", response_model=Cliente)
def api_obter_cliente(cliente_id: int) -> Cliente:
    return obter_cliente(cliente_id)


@app.put("/clientes/{cliente_id}", response_model=Cliente)
def api_atualizar_cliente(cliente_id: int, atualizacao: ClienteUpdate) -> Cliente:
    return atualizar_cliente(cliente_id, atualizacao)


@app.delete("/clientes/{cliente_id}", status_code=204, response_class=Response)
def api_deletar_cliente(cliente_id: int) -> Response:
    deletar_cliente(cliente_id)
    return Response(status_code=204)


# Produtos

@app.post("/produtos/", response_model=Produto, status_code=201)
def api_criar_produto(produto: Produto) -> Produto:
    return criar_produto(produto)


@app.get("/produtos/", response_model=List[Produto])
def api_listar_produtos() -> List[Produto]:
    return listar_produtos()


@app.get("/produtos/{produto_id}", response_model=Produto)
def api_obter_produto(produto_id: int) -> Produto:
    return obter_produto(produto_id)


@app.put("/produtos/{produto_id}", response_model=Produto)
def api_atualizar_produto(produto_id: int, atualizacao: ProdutoUpdate) -> Produto:
    return atualizar_produto(produto_id, atualizacao)


@app.delete("/produtos/{produto_id}", status_code=204, response_class=Response)
def api_deletar_produto(produto_id: int) -> Response:
    deletar_produto(produto_id)
    return Response(status_code=204)


# Vendas

@app.post("/vendas/", response_model=Venda, status_code=201)
def api_criar_venda(venda: Venda) -> Venda:
    return criar_venda(venda)


@app.get("/vendas/", response_model=List[Venda])
def api_listar_vendas() -> List[Venda]:
    return listar_vendas()


@app.get("/vendas/{venda_id}", response_model=Venda)
def api_obter_venda(venda_id: int) -> Venda:
    return obter_venda(venda_id)


@app.put("/vendas/{venda_id}", response_model=Venda)
def api_atualizar_venda(venda_id: int, atualizacao: VendaUpdate) -> Venda:
    return atualizar_venda(venda_id, atualizacao)


@app.delete("/vendas/{venda_id}", status_code=204, response_class=Response)
def api_deletar_venda(venda_id: int) -> Response:
    deletar_venda(venda_id)
    return Response(status_code=204)


# --- CLI interface ---


def cli(args: Optional[List[str]] = None) -> int:
    """Interface de linha de comando para o sistema de gestão de vendas."""

    parser = ArgumentParser(description="Sistema de Gestão de Vendas CLI")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Inicia o servidor FastAPI (uvicorn) com a aplicação `app`.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor (padrão: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor (padrão: 8000).")
    subparsers = parser.add_subparsers(dest="comando", required=False)

    # Comando init para criar banco de dados
    subparsers.add_parser(
        "init", help="Inicializa o banco de dados criando as tabelas necessárias."
    )

    # Outras funções CLI poderiam ser adicionadas aqui: listar clientes, criar cliente, etc.
    # Por escopo, manteremos apenas inicialização do banco.

    parsed_args = parser.parse_args(args)

    if getattr(parsed_args, "serve", False):
        try:
            import uvicorn
        except Exception as exc:  # pragma: no cover
            print("Erro: uvicorn não está instalado. Instale com: pip install uvicorn", file=sys.stderr)
            raise exc

        uvicorn.run(app, host=parsed_args.host, port=parsed_args.port)
        return 0

    if parsed_args.comando == "init":
        init_db()
        print("Banco de dados inicializado com sucesso.")
        return 0

    parser.print_help()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """
    Ponto de entrada CLI.
    Exemplo de uso:
      python sistema_gerado.py init
    """
    return cli(argv)


if __name__ == "__main__":
    sys.exit(main())
