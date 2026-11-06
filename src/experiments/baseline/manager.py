from models import Emenda
from typing import List
from experiments.llm.prompts import EXTRAIR_EMENDAS_RELATORIO_PROMPT

class BaselineManager:
    def __init__(self, llm_client, downloader, text_extractor):
        self.llm_client = llm_client
        self.downloader = downloader
        self.text_extractor = text_extractor

    def get_amendments_status_dict(self, amendments: List[Emenda]):
        status_dict = {}
        for amendment in amendments:
            status_dict[amendment.id] = {
                "numero": amendment.numero,
                "tipo": amendment.tipo,
                "orgao": amendment.orgao,
                "data_apresentacao": amendment.data_apresentacao,
                "status": None,
                "justification": None
            }
        return status_dict

    def get_amendments_status(self, report_text):
        return self.llm_client.call(EXTRAIR_EMENDAS_RELATORIO_PROMPT, report_text)

    def update_amendments_status(self, extracted_status, status_dict):
        for amendment_id, status in extracted_status.items():
            if amendment_id in status_dict:
                status_dict[amendment_id]["status"] = status