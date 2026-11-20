from pydantic import BaseModel, Field, computed_field


class Criterio(BaseModel):
    justificativa: str = Field(
        description=(
            "Análise objetiva comparando o texto gerado com o texto de referência "
            "para este critério, citando acertos, omissões ou divergências específicas."
        )
    )
    nota: int = Field(
        ge=1,
        le=5,
        description="Nota inteira de 1 (muito ruim) a 5 (excelente) conforme a rubrica.",
    )


class AvaliacaoLLM(BaseModel):
    fidelidade_normativa: Criterio = Field(
        description=(
            "Preservação do sentido jurídico, coerência interna, remissões válidas "
            "e ausência de distorções ou alucinações."
        )
    )
    completude_consolidacao: Criterio = Field(
        description=(
            "Presença de todas as modificações, acréscimos, supressões e cláusulas "
            "finais (vigência e revogação) esperadas na referência."
        )
    )
    preservacao_inalterados: Criterio = Field(
        description=(
            "Manutenção intacta de todos os dispositivos que não sofreram alteração "
            "na referência, sem reescritas, truncamentos ou supressões acidentais."
        )
    )
    integridade_estrutural: Criterio = Field(
        description=(
            "Consistência da hierarquia legislativa (livros, títulos, capítulos, seções, "
            "artigos, parágrafos, incisos, alíneas e itens), ordem e numeração."
        )
    )
    tecnica_legislativa: Criterio = Field(
        description=(
            "Conformidade às convenções da LC nº 95/1998 e do MRPR presentes na referência: "
            "aspas, (NR), linhas pontilhadas em alterações parciais e precisão redacional."
        )
    )
    resumo_erros: str = Field(
        description="Síntese curta dos principais desvios encontrados (ou 'Nenhum desvio relevante')."
    )

    @computed_field
    @property
    def nota_media(self) -> float:
        notas = [
            self.fidelidade_normativa.nota,
            self.completude_consolidacao.nota,
            self.preservacao_inalterados.nota,
            self.integridade_estrutural.nota,
            self.tecnica_legislativa.nota,
        ]
        return round(sum(notas) / len(notas), 4)