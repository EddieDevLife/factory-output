import sys
from datetime import datetime
from typing import List, Optional
import argparse

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base

SISTEMA_DB_PATH = "vendas.db"

# Configuração do banco SQLite com SQLAlchemy
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SISTEMA_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item = Column(String, nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)
    valor_unitario = Column(Float, nullable=False)
    data_venda = Column(DateTime, nullable=False, index=True)


Base.metadata.create_all(bind=engine)


# Pydantic models com Pydantic v2
class VendaBase(BaseModel):
    item: str
    quantidade: int
    valor_unitario: float
    data_venda: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("quantidade")
    @classmethod
    def quantidade_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("quantidade deve ser maior que zero")
        return v

    @field_validator("valor_unitario")
    @classmethod
    def valor_unitario_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("valor_unitario deve ser maior que zero")
        return v


class VendaCreate(VendaBase):
    pass


class VendaUpdate(BaseModel):
    item: Optional[str] = None
    quantidade: Optional[int] = None
    valor_unitario: Optional[float] = None
    data_venda: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("quantidade")
    @classmethod
    def quantidade_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("quantidade deve ser maior que zero")
        return v

    @field_validator("valor_unitario")
    @classmethod
    def valor_unitario_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("valor_unitario deve ser maior que zero")
        return v


class VendaRead(VendaBase):
    id: int


# FastAPI app
app = FastAPI(title="Sistema de Gestão de Vendas - MVP", version="1.0")


# Dependency to get DB session per request
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/vendas", response_model=VendaRead, status_code=status.HTTP_201_CREATED)
def criar_venda(venda: VendaCreate, db: Session = Depends(get_db)):
    db_venda = Venda(
        item=venda.item,
        quantidade=venda.quantidade,
        valor_unitario=venda.valor_unitario,
        data_venda=venda.data_venda,
    )
    db.add(db_venda)
    db.commit()
    db.refresh(db_venda)
    return db_venda


@app.get("/vendas", response_model=List[VendaRead])
def listar_vendas(db: Session = Depends(get_db)):
    vendas = db.query(Venda).all()
    return vendas


@app.get("/vendas/{id}", response_model=VendaRead)
def consultar_venda(id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == id).first()
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    return venda


@app.put("/vendas/{id}", response_model=VendaRead)
def atualizar_venda(id: int, venda_update: VendaUpdate, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == id).first()
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")

    update_data = venda_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(venda, key, value)

    db.add(venda)
    db.commit()
    db.refresh(venda)
    return venda


@app.delete("/vendas/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_venda(id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == id).first()
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    db.delete(venda)
    db.commit()
    return None


def main(argv=None):
    import sys

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Sistema de Gestão de Vendas - MVP\n"
        "Use --serve para iniciar servidor FastAPI."
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Iniciar servidor FastAPI localmente na porta 8000",
    )
    args = parser.parse_args(argv)

    if args.serve:
        import uvicorn

        uvicorn.run("output.sistema_gerado:app", host="127.0.0.1", port=8000, reload=False)
        sys.exit(0)

    print(
        "Sistema de Gestão de Vendas - MVP\n"
        "Execute com --serve para iniciar o servidor FastAPI local na porta 8000\n"
        "Exemplo:\n"
        "  python output/sistema_gerado.py --serve\n"
        "Documentação da API estará disponível em http://127.0.0.1:8000/docs após iniciar servidor."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()