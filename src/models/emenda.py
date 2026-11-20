from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class StatusEmenda(str, Enum):
    APROVADA = "Aprovada"
    REJEITADA = "Rejeitada"
    APROVADA_PARCIALMENTE = "Aprovada parcialmente"
    PREJUDICADA = "Prejudicada"
    RETIRADA = "Retirada"
    NAO_APRECIADA = "Não apreciada"

class DeliberacaoEmenda(BaseModel):
    id_emenda: int = Field(description="Número identificador inteiro da emenda (ex: 1, 2, 3).")
    status: Optional[StatusEmenda] = Field(
        default=None,
        description="Resultado final da deliberação do relator conforme a Conclusão do Voto."
    )
    justificativa: Optional[str] = Field(
        default=None,
        description="Resumo objetivo (1-2 frases) dos argumentos do relator que fundamentaram a decisão."
    )


class DeliberacoesEmenda(BaseModel):
    deliberacoes: List[DeliberacaoEmenda] = Field(
        description="Lista completa de todas as emendas deliberadas no relatório, em ordem crescente de id_emenda."
    )

class TipoMudancaEmenda(Enum):
    ADITIVA = "Aditiva"
    SUPRESSIVA = "Supressiva"
    MODIFICATIVA = "Modificativa"

class MudancaEmenda(BaseModel):
    tipo: TipoMudancaEmenda = Field(
        description="Tipo da operação na árvore XML: Aditiva, Modificativa ou Supressiva."
    )
    id_lexml: str = Field(
        description="Valor EXATO do atributo 'id' presente no XML do texto inicial."
    )
    paragrafos_xhtml: list[str] = Field(
        default_factory=list,
        description="Lista de parágrafos em texto plano (vazia [] para Supressiva).",
    )

class MudancasEmenda(BaseModel):
    mudancas: list[MudancaEmenda]



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
