from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
import sys

"""
Módulo do Sistema de Gestão de Vendas.
Define modelos Pydantic 2 e a API FastAPI para operações básicas.
"""

# Base é o alias para o BaseModel do pydantic para facilitar a migração e referências futuras
Base = BaseModel

class Venda(Base):
    id: int
    produto: str
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)

class VendaCreate(Base):
    produto: str
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)

class VendaUpdate(Base):
    produto: Optional[str] = None
    quantidade: Optional[int] = Field(None, gt=0)
    preco_unitario: Optional[float] = Field(None, gt=0)

app = FastAPI()

# Simples armazenamento em memória para exemplo funcional
_vendas: List[Venda] = []
_venda_id_counter = 1

@app.get("/")
def raiz():
    """
    Endpoint raiz.
    Retorna mensagem de boas-vindas do sistema.
    """
    return {"msg": "Sistema de Gestão de Vendas API está no ar."}

@app.get("/vendas/", response_model=List[Venda])
def listar_vendas():
    """
    Lista todas as vendas cadastradas.
    """
    return _vendas

@app.get("/vendas/{venda_id}", response_model=Venda)
def obter_venda(venda_id: int):
    """
    Obtém a venda pelo seu id.
    """
    for venda in _vendas:
        if venda.id == venda_id:
            return venda
    raise HTTPException(status_code=404, detail="Venda não encontrada")

@app.post("/vendas/", response_model=Venda, status_code=201)
def criar_venda(venda_data: VendaCreate):
    """
    Cria uma nova venda.
    """
    global _venda_id_counter
    venda = Venda(id=_venda_id_counter, **venda_data.model_dump())
    _vendas.append(venda)
    _venda_id_counter += 1
    return venda

@app.put("/vendas/{venda_id}", response_model=Venda)
def atualizar_venda(venda_id: int, venda_data: VendaUpdate):
    """
    Atualiza os dados de uma venda existente pelo id.
    """
    for idx, venda in enumerate(_vendas):
        if venda.id == venda_id:
            atualizados = venda.model_copy(update=venda_data.model_dump(exclude_unset=True))
            _vendas[idx] = atualizados
            return atualizados
    raise HTTPException(status_code=404, detail="Venda não encontrada")

@app.delete("/vendas/{venda_id}", status_code=204)
def remover_venda(venda_id: int):
    """
    Remove uma venda pelo seu id.
    """
    for idx, venda in enumerate(_vendas):
        if venda.id == venda_id:
            del _vendas[idx]
            return
    raise HTTPException(status_code=404, detail="Venda não encontrada")


def main(argv=None):
    """
    Perfil de execução CLI para o sistema.
    Sem argumentos imprime ajuda.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        print(
            "Uso:\n"
            "  Nenhum argumento: imprime esta ajuda.\n"
            "  A aplicação principal é FastAPI - execute com uvicorn output.sistema_gerado:app --reload\n"
        )
        return 0
    else:
        print(f"Argumentos não reconhecidos: {argv}")
        return 1


if __name__ == "__main__":
    sys.exit(main())