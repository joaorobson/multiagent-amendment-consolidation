import re

from models import Emenda, DeliberacaoEmenda, EdicaoEmenda, StatusEmenda
from typing import Dict, List, Dict
from experiments.llm.prompts import PROMPT_APLICAR_EMENDAS, PROMPT_EXTRAIR_EMENDAS_RELATORIO, PROMPT_BUSCAR_EDICOES

class BaselineManager:
    def __init__(self, llm_client, downloader, text_extractor):
        self.llm_client = llm_client
        self.downloader = downloader
        self.text_extractor = text_extractor

    def get_amendments_status(self, report_text) -> Dict[int, DeliberacaoEmenda]:
        return self.llm_client.call(PROMPT_EXTRAIR_EMENDAS_RELATORIO)

    def update_amendments_status(self, amendments: Dict[int, Emenda], extracted_status: Dict[int, DeliberacaoEmenda]):
        for amendment_id, deliberacao in extracted_status.items():
            print('deliberacao', deliberacao)
            if amendment_id in amendments:
                amendments[amendment_id].deliberacao = deliberacao

    def apply_amendments(self, amendments, initial_text):
        return self.llm_client.call(PROMPT_APLICAR_EMENDAS)

    def get_changes(self, amendment, initial_text) -> List[EdicaoEmenda]:
        changes = self.llm_client.call(PROMPT_BUSCAR_EDICOES)
        return changes.get(amendment.id, [])

    def _normalizar_bloco(self, texto: str) -> str:
        """
        Padroniza quebras de linha e remove espaços inúteis no início e no fim 
        de cada linha, ignorando também linhas totalmente vazias extras.
        """
        if not texto:
            return ""
        
        # Normaliza quebras de linha para \n padrão
        texto_limpo = texto.replace("\r\n", "\n").replace("\r", "\n")
        
        # Divide em linhas, remove espaços excedentes das pontas de cada linha (strip)
        linhas = [linha.strip() for linha in texto_limpo.splitlines()]
        
        # Recompõe o texto mantendo apenas linhas que possuem conteúdo
        return "\n".join([l for l in linhas if l])

    def apply_amendment_change(self, change: EdicaoEmenda, initial_text: str) -> str:
        """
        Aplica a mudança do baseline com alta resiliência a espaços finais de linha,
        travessões e quebras de PDF.
        """
        if not change.bloco_busca or not change.bloco_substituicao:
            return initial_text

        # 1. Tentativa Exata Tradicional (caso o LLM tenha acertado milimetricamente)
        if change.bloco_busca in initial_text:
            return initial_text.replace(change.bloco_busca, change.bloco_substituicao)

        # 2. Tentativa por Normalização de Linhas (Remove espaços nas pontas e quebras sujas)
        texto_norm = self._normalizar_bloco(initial_text)
        busca_norm = self._normalizar_bloco(change.bloco_busca)
        subst_norm = self._normalizar_bloco(change.bloco_substituicao)

        if busca_norm in texto_norm:
            # Substitui no texto normalizado
            return texto_norm.replace(busca_norm, subst_norm)

        # 3. Fallback Avançado por Regex Flexível (caso haja pequenas variações internas)
        # Escapa o bloco de busca normalizado para usar em expressão regular
        bloco_escapado = re.escape(busca_norm)
        
        # Transforma qualquer espaço ou quebra interna na regex para aceitar múltiplos espaços (\s+)
        padrao_flexivel = re.sub(r'\\ ', r'\\s+', bloco_escapado)
        padrao_flexivel = re.sub(r'\\n', r'\\s+', padrao_flexivel)

        match = re.search(padrao_flexivel, texto_norm)
        if match:
            inicio, fim = match.span()
            return texto_norm[:inicio] + subst_norm + texto_norm[fim:]

        # 4. Falha Crítica Controlada (Métrica para a Tese)
        print(f"Aviso [Baseline]: Não foi possível localizar o bloco de busca da emenda {change.emenda_id}.")
        return initial_text

    def get_approved_amendments(self, amendments: Dict[int, Emenda]) -> List[Emenda]:
        approved_amendments = []
        for amendment in amendments.values():
            if amendment.deliberacao and amendment.deliberacao.status in (StatusEmenda.APROVADA, StatusEmenda.APROVADA_PARCIALMENTE):
                approved_amendments.append(amendment)
        return approved_amendments