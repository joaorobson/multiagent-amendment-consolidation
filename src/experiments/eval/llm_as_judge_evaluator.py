from typing import Any

from .base_evaluator import BaseEvaluator
from experiments.lexml import LexMLParserWrapper
from experiments.llm import BaseLLMClient
from experiments.llm.prompts import LLM_AS_A_JUDGE_SYSTEM_PROMPT
from models import AvaliacaoLLM


class LLMAsAJudgeEvaluator(BaseEvaluator):
    CRITERIOS = (
        "fidelidade_normativa",
        "completude_consolidacao",
        "preservacao_inalterados",
        "integridade_estrutural",
        "tecnica_legislativa",
    )

    def __init__(
        self,
        name: str,
        llm_client: BaseLLMClient,
        lexml_parser: LexMLParserWrapper,
        max_artigos_sem_chunk: int = 15,
        chunk_size: int = 10,
    ) -> None:
        super().__init__(name)
        self.llm_client = llm_client
        self.lexml_parser = lexml_parser
        self.max_artigos_sem_chunk = max_artigos_sem_chunk
        self.chunk_size = chunk_size

    def _avaliar_bloco(self, txt_chunk: str, txt_ref_chunk: str) -> dict[str, Any]:
        user_prompt = (
            "Avalie o texto consolidado gerado comparando-o com o texto oficial de referência.\n"
            "<texto_referencia>\n"
            f"{txt_ref_chunk}\n"
            "</texto_referencia>\n\n"
            "<texto_gerado>\n"
            f"{txt_chunk}\n"
            "</texto_gerado>"
        )

        result: AvaliacaoLLM = self.llm_client.call(
            system_prompt=LLM_AS_A_JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_format=AvaliacaoLLM,
        )
        return result.model_dump()

    @classmethod
    def _resultado_bloco_identico(cls) -> dict[str, Any]:
        res: dict[str, Any] = {
            c: {"justificativa": "Bloco textualmente idêntico à referência.", "nota": 5}
            for c in cls.CRITERIOS
        }
        res["resumo_erros"] = "Nenhum desvio relevante"
        res["nota_media"] = 5.0
        return res

    @staticmethod
    def _media_ponderada(itens: list[tuple[dict[str, Any], int]], criterio: str) -> float:
        total = sum(peso for _, peso in itens)
        return round(sum(r[criterio]["nota"] * peso for r, peso in itens) / total, 4)

    def eval(self, txt: str, txt_ref: str) -> dict[str, Any]:
        txts, txts_ref = self.lexml_parser.alinhar_artigos(txt, txt_ref)
        if not txts:
            raise ValueError("Nenhum artigo encontrado para avaliação entre o XML gerado e a referência.")

        tamanho_bloco = (
            len(txts) if len(txts) <= self.max_artigos_sem_chunk else self.chunk_size
        )

        todos_blocos: list[tuple[dict[str, Any], int]] = []
        blocos_divergentes: list[tuple[dict[str, Any], int]] = []

        for i in range(0, len(txts), tamanho_bloco):
            bloco_gerado = txts[i : i + tamanho_bloco]
            bloco_ref = txts_ref[i : i + tamanho_bloco]
            peso = len(bloco_gerado)

            if bloco_gerado == bloco_ref:
                res = self._resultado_bloco_identico()
                todos_blocos.append((res, peso))
                continue

            txt_chunk = "\n\n".join(t if t else "[ARTIGO AUSENTE]" for t in bloco_gerado)
            txt_ref_chunk = "\n\n".join(t if t else "[ARTIGO AUSENTE]" for t in bloco_ref)

            res = self._avaliar_bloco(txt_chunk, txt_ref_chunk)
            todos_blocos.append((res, peso))
            blocos_divergentes.append((res, peso))

        media_global = {
            c: self._media_ponderada(todos_blocos, c) for c in self.CRITERIOS
        }
        media_global["nota_media"] = round(
            sum(media_global.values()) / len(self.CRITERIOS), 4
        )

        nota_minima = {
            c: min(r[c]["nota"] for r, _ in todos_blocos) for c in self.CRITERIOS
        }
        nota_minima["nota_media"] = min(r["nota_media"] for r, _ in todos_blocos)

        if blocos_divergentes:
            media_divergentes = {
                c: self._media_ponderada(blocos_divergentes, c) for c in self.CRITERIOS
            }
            media_divergentes["nota_media"] = round(
                sum(media_divergentes.values()) / len(self.CRITERIOS), 4
            )
        else:
            media_divergentes = None

        return {
            "total_artigos": len(txts),
            "total_blocos": len(todos_blocos),
            "blocos_identicos": len(todos_blocos) - len(blocos_divergentes),
            "blocos_divergentes": len(blocos_divergentes),
            "media_global": media_global,
            "media_divergentes": media_divergentes,
            "nota_minima": nota_minima,
            "detalhes_blocos": [r for r, _ in todos_blocos],
        }