from models import StatusEmenda
from .prompts import EXTRAIR_EMENDAS_RELATORIO_PROMPT

class FakeLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def call(self, prompt, texto):
        if prompt == EXTRAIR_EMENDAS_RELATORIO_PROMPT:
            return {847: StatusEmenda.APROVADA, 848: StatusEmenda.REJEITADA}