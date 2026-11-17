from pydantic import BaseModel, Field
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


class TipoMudancaEmenda(Enum):
    ADITIVA = "Aditiva"
    SUPRESSIVA = "Supressiva"
    MODIFICATIVA = "Modificativa"

class MudancaEmenda(BaseModel):
    tipo: TipoMudancaEmenda
    id_lexml: str
    paragrafos_xhtml: list[str] = Field(
        default_factory=list
    )
    xml: Optional[str] = ""


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
