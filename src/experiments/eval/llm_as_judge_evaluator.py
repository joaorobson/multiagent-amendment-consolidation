from .base_evaluator import BaseEvaluator
from experiments.llm import BaseLLMClient
from experiments.llm.prompts import LLM_AS_A_JUDGE_SYSTEM_PROMPT
from models import AvaliacaoLLM

class LLMAsAJudgeEvaluator(BaseEvaluator):
    def __init__(self, name: str, llm_client: BaseLLMClient) -> None:
        super().__init__(name)
        self.llm_client = llm_client
    
    def eval(self, txt: str, txt_ref: str) -> dict:
        user_prompt = f"""Avalie o texto consolidado gerado comparando-o com o texto oficial de referência.
            <texto_referencia>
            {txt_ref}
            </texto_referencia>

            <texto_gerado>
            {txt}
            </texto_gerado>
        """

        result: AvaliacaoLLM = self.llm_client.call(
            system_prompt=LLM_AS_A_JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            text_format=AvaliacaoLLM,
        )

        return result.model_dump()