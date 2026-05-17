import sys
import argparse
import datetime
from typing import List, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator, ValidationError
from sqlmodel import Field, Session, SQLModel, create_engine, select

SISTEMA_DB_PATH = "tarefas.db"
app = FastAPI(title="API de Gerenciamento de Tarefas com Prioridade")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=FileResponse, include_in_schema=False)
def serve_frontend():
    return FileResponse("index.html")

# Enum para status das tarefas
class Status(str, Enum):
    pendente = "pendente"
    concluido = "concluído"

# Modelo SQLAlchemy / SQLModel da tabela Tarefa
class Tarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    descricao: str
    prazo: datetime.date
    impacto: int
    status: Status

# Pydantic - Modelo base com validações compartilhadas
class TarefaBase(BaseModel):
    titulo: str
    descricao: str
    prazo: datetime.date
    impacto: int
    status: Status

    model_config = ConfigDict(from_attributes=True)

    @field_validator("impacto")
    @classmethod
    def impacto_valido(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("impacto deve estar entre 1 e 10")
        return v

    @field_validator("prazo")
    @classmethod
    def prazo_no_futuro(cls, v):
        hoje = datetime.date.today()
        if v < hoje:
            raise ValueError("prazo deve ser uma data igual ou posterior a hoje")
        return v

# Modelo usado para criação
class TarefaCreate(TarefaBase):
    pass

# Modelo para resposta (inclui id)
class TarefaRead(TarefaBase):
    id: int

# Modelo para atualização parcial via PUT (todos opcionais com default None)
class TarefaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    prazo: Optional[datetime.date] = None
    impacto: Optional[int] = None
    status: Optional[Status] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("impacto")
    @classmethod
    def impacto_valido(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError("impacto deve estar entre 1 e 10")
        return v

    @field_validator("prazo")
    @classmethod
    def prazo_no_futuro(cls, v):
        if v is not None:
            hoje = datetime.date.today()
            if v < hoje:
                raise ValueError("prazo deve ser uma data igual ou posterior a hoje")
        return v

# Criação do engine e sessão do banco com caminho configurável
engine = create_engine(f"sqlite:///{SISTEMA_DB_PATH}", echo=False, connect_args={"check_same_thread": False})

def criar_bd_e_tabelas():
    SQLModel.metadata.create_all(engine)

# Dependência para obter sessão
def get_session():
    with Session(engine) as session:
        yield session

# Serviço para cálculo do Score
def calcular_score(impacto: int, prazo: datetime.date) -> int:
    hoje = datetime.date.today()
    dias_ate_prazo = (prazo - hoje).days
    score = (impacto * 2) - dias_ate_prazo
    return score

# ------------------------------------------
# Rotas da API
# ------------------------------------------

@app.post("/tarefas", response_model=TarefaRead, status_code=201)
def criar_tarefa(tarefa_in: TarefaCreate, session: Session = Depends(get_session)):
    # Validacões já feitas por Pydantic
    tarefa = Tarefa(
        titulo=tarefa_in.titulo,
        descricao=tarefa_in.descricao,
        prazo=tarefa_in.prazo,
        impacto=tarefa_in.impacto,
        status=tarefa_in.status,
    )
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.get("/tarefas", response_model=List[TarefaRead])
def listar_tarefas(status: Optional[Status] = Query(None), session: Session = Depends(get_session)):
    query = select(Tarefa)
    if status is not None:
        query = query.where(Tarefa.status == status)
    query = query.order_by(Tarefa.id)
    tarefas = session.exec(query).all()
    return tarefas

@app.get("/tarefas/prioridade", response_model=List[TarefaRead])
def listar_tarefas_prioridade(session: Session = Depends(get_session)):
    tarefas = session.exec(select(Tarefa)).all()
    hoje = datetime.date.today()

    # Enriquecer com score
    tarefas_score = []
    for t in tarefas:
        score = calcular_score(t.impacto, t.prazo)
        tarefas_score.append((score, t))

    # Ordenar decrescente pelo score
    tarefas_ordenadas = [tarefa for score, tarefa in sorted(tarefas_score, key=lambda x: x[0], reverse=True)]
    return tarefas_ordenadas

@app.put("/tarefas/{id}", response_model=TarefaRead)
def atualizar_tarefa(id: int, tarefa_update: TarefaUpdate, session: Session = Depends(get_session)):
    tarefa = session.get(Tarefa, id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    dados_update = tarefa_update.model_dump(exclude_unset=True)
    try:
        # Validação forçada para os campos informados no update:
        # Cria um modelo completo para validar campos que ficaram idempotentes e não vazios
        # Carregar dados atuais e aplicar update no dict e validar a partir dessa composição
        dados_completos = {
            "titulo": tarefa.titulo,
            "descricao": tarefa.descricao,
            "prazo": tarefa.prazo,
            "impacto": tarefa.impacto,
            "status": tarefa.status,
        }
        dados_completos.update(dados_update)
        TarefaBase.model_validate(dados_completos)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())

    for chave, valor in dados_update.items():
        setattr(tarefa, chave, valor)

    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.delete("/tarefas/{id}", status_code=204)
def deletar_tarefa(id: int, session: Session = Depends(get_session)):
    tarefa = session.get(Tarefa, id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    session.delete(tarefa)
    session.commit()
    return None

# ------------------------------------------
# Mensagem no terminal quando executado diretamente
# ------------------------------------------
def main():
    msg = """
API de Gerenciamento de Tarefas com Prioridade.

Para rodar o servidor use o comando:
    python output/sistema_gerado.py --serve

Documentação interativa disponível na rota:
    http://127.0.0.1:8000/docs

Exemplos de chamadas cURL:

1. Criar tarefa:
curl -X POST "http://127.0.0.1:8000/tarefas" -H "Content-Type: application/json" -d \\
'{
  "titulo": "Comprar leite",
  "descricao": "Comprar 2 litros de leite no mercado",
  "prazo": "2024-12-31",
  "impacto": 5,
  "status": "pendente"
}'

2. Listar todas tarefas:
curl "http://127.0.0.1:8000/tarefas"

3. Listar tarefas ordenadas por prioridade:
curl "http://127.0.0.1:8000/tarefas/prioridade"

4. Atualizar uma tarefa por id:
curl -X PUT "http://127.0.0.1:8000/tarefas/1" -H "Content-Type: application/json" -d \\
'{
  "status": "concluído"
}'

"""
    print(msg.strip())

if __name__ == "__main__":
    criar_bd_e_tabelas()

    parser = argparse.ArgumentParser(description="API de Gerenciamento de Tarefas com Prioridade")
    parser.add_argument("--serve", action="store_true", help="Executar o servidor com Uvicorn")

    args = parser.parse_args()
    if args.serve:
        import uvicorn
        uvicorn.run("sistema_gerado:app", host="0.0.0.0", port=8000, reload=False)
    else:
        main()
        sys.exit(0)