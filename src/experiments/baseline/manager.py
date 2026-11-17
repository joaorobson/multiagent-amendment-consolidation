import re

from models import Emenda, DeliberacaoEmenda, MudancaEmenda, StatusEmenda, TipoMudancaEmenda
from typing import Dict, List, Dict
from experiments.llm.prompts import PROMPT_APLICAR_EMENDAS, PROMPT_EXTRAIR_EMENDAS_RELATORIO, PROMPT_BUSCAR_EDICOES
from lxml import etree

class BaselineManager:
    def __init__(self, llm_client, downloader, text_extractor):
        self.llm_client = llm_client
        self.downloader = downloader
        self.text_extractor = text_extractor
        self.parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8")
        self.ns = {"lex": "http://www.lexml.gov.br/1.0"}
    def get_amendments_status(self, report_text) -> Dict[int, DeliberacaoEmenda]:
        return self.llm_client.call(PROMPT_EXTRAIR_EMENDAS_RELATORIO)

    def update_amendments_status(self, amendments: Dict[int, Emenda], extracted_status: Dict[int, DeliberacaoEmenda]):
        for amendment_id, deliberacao in extracted_status.items():
            print('deliberacao', deliberacao)
            if amendment_id in amendments:
                amendments[amendment_id].deliberacao = deliberacao

    def apply_amendments(self, amendments, initial_text):
        return self.llm_client.call(PROMPT_APLICAR_EMENDAS)

    def get_changes(self, amendment, initial_text) -> List[MudancaEmenda]:
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

    def _prefixar_ids_fragmento(self, fragmento: etree._Element, id_pai: str):
        """
        Ajusta os IDs gerados isoladamente pelo parseArticulacao (ex: 'inc6', 'par1u')
        para herdarem o prefixo do dispositivo pai no XML original (ex: 'art6_cpt_inc6', 'art6_par1u').
        """
        for el in fragmento.iter():
            id_atual = el.get("id")
            if id_atual and not id_atual.startswith(id_pai):
                el.set("id", f"{id_pai}_{id_atual}")


    def apply_amendment_change(self, change: MudancaEmenda, xml_string: str) -> str:
        """
        Aplica a mudança da emenda no XML estruturado usando o fragmento já parseado em `change.xml`.
        """
        if not change.id_lexml:
            print(f"Aviso [Baseline XML]: Emenda sem id_lexml definido.")
            return xml_string

        try:
            tree = etree.fromstring(xml_string.encode("utf-8"), parser=self.parser)

            # Busca o elemento alvo por ID em qualquer nível da árvore
            elementos_alvo = tree.xpath(f"//*[@id='{change.id_lexml}']", namespaces=self.ns)
            if not elementos_alvo:
                elementos_alvo = tree.xpath(f"//*[@id='{change.id_lexml}']")

            if not elementos_alvo:
                print(f"Aviso [Baseline XML]: Elemento com id '{change.id_lexml}' não encontrado.")
                return xml_string

            alvo = elementos_alvo[0]
            pai = alvo.getparent()
            tag_alvo = etree.QName(alvo).localname

            # 1. Supressão
            if change.tipo == TipoMudancaEmenda.SUPRESSIVA:
                if pai is not None:
                    pai.remove(alvo)
                    print(f"Sucesso [Baseline]: Dispositivo {tag_alvo} ({change.id_lexml}) suprimido.")

            # 2. Modificação ou Adição (usando change.xml já gerado pelo parse_articulacao)
            else:
                if not change.xml:
                    print(f"Aviso [Baseline XML]: change.xml vazio para {change.id_lexml}.")
                    return xml_string

                articulacao_fragmento = etree.fromstring(change.xml.encode("utf-8"), parser=self.parser)
                novos_nos = list(articulacao_fragmento)

                if not novos_nos:
                    print(f"Aviso [Baseline XML]: Nenhum nó encontrado em change.xml para {change.id_lexml}.")
                    return xml_string

                # Se o pai do alvo não for <Articulacao> (ou seja, é um sub-dispositivo dentro de um Artigo/Caput/Parágrafo),
                # prefixa os IDs do fragmento com o ID do pai para manter a hierarquia (ex: 'art6_cpt' + 'inc6' -> 'art6_cpt_inc6')
                id_pai = pai.get("id") if pai is not None else None
                if id_pai:
                    for no in novos_nos:
                        self._prefixar_ids_fragmento(no, id_pai)

                if change.tipo == TipoMudancaEmenda.MODIFICATIVA:
                    idx = pai.index(alvo)
                    pai.remove(alvo)
                    for i, novo_no in enumerate(novos_nos):
                        pai.insert(idx + i, novo_no)

                elif change.tipo == TipoMudancaEmenda.ADITIVA:
                    ref = alvo
                    for novo_no in novos_nos:
                        ref.addnext(novo_no)
                        ref = novo_no

                print(f"Sucesso [Baseline]: Dispositivo {tag_alvo} ({change.id_lexml}) atualizado ({change.tipo.value}).")

            return etree.tostring(
                tree,
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True,
            ).decode("utf-8")

        except Exception as e:
            print(f"Erro crítico [Baseline XML] ao processar o XML: {e}")
            return xml_string

    def get_approved_amendments(self, amendments: Dict[int, Emenda]) -> List[Emenda]:
        approved_amendments = []
        for amendment in amendments.values():
            if amendment.deliberacao and amendment.deliberacao.status in (StatusEmenda.APROVADA, StatusEmenda.APROVADA_PARCIALMENTE):
                approved_amendments.append(amendment)
        return approved_amendments