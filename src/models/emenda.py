from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class StatusEmenda(Enum):
    APROVADA = "Aprovada"
    REJEITADA = "Rejeitada"
    APROVADA_PARCIALMENTE = "Aprovada parcialmente"
    PREJUDICADA = "Prejudicada"
    RETIRADA = "Retirada"
    NAO_APRECIADA = "Não apreciada"

class DeliberacaoEmenda(BaseModel):
    status: Optional[StatusEmenda] = None
    justificativa: Optional[str] = None

class EdicaoEmenda(BaseModel):
    bloco_busca: str
    bloco_substituicao: str


class Emenda(BaseModel):
    id: int
    id_proposicao: int
    numero: int
    tipo: Optional[str] = None
    orgao: Optional[str] = None
    data_apresentacao: datetime
    id_original: int
    descricao: Optional[str] = None
    ementa: Optional[str] = None
    url_doc: Optional[str] = None
    url_metadados: Optional[str] = None
    texto: Optional[str] = None
    deliberacao: Optional[DeliberacaoEmenda] = None
