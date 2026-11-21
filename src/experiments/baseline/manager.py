import re

from models import Emenda, DeliberacaoEmenda, MudancaEmenda, StatusEmenda, TipoMudancaEmenda, DeliberacoesEmenda, MudancasEmenda
from typing import Dict, List, Dict
from experiments.llm.prompts import SYSTEM_PROMPT_APLICACAO_EMENDAS, SYSTEM_PROMPT_EXTRACAO_EMENDAS_RELATORIO
from lxml import etree

class BaselineManager:
    def __init__(self, llm_client, lexml_parser):
        self.llm_client = llm_client
        self.xml_parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8")
        self.lexml_parser = lexml_parser
        self.ns = {"lex": "http://www.lexml.gov.br/1.0"}

    def get_amendments_status(self, report_text) -> Dict[int, DeliberacaoEmenda]:
        user_prompt = f"""Extraia a deliberação final de todas as emendas contidas no relatório legislativo abaixo:

        <relatorio>
        {report_text}
        </relatorio>"""
        deliberacoes = self.llm_client.call(SYSTEM_PROMPT_EXTRACAO_EMENDAS_RELATORIO, user_prompt, response_format=DeliberacoesEmenda)
        return {em.id_emenda: em for em in deliberacoes.deliberacoes}

    def update_amendments_status(self, amendments: Dict[int, Emenda], extracted_status: Dict[int, DeliberacaoEmenda]):
        for amendment_id, deliberacao in extracted_status.items():
            print('deliberacao', deliberacao)
            if amendment_id in amendments:
                amendments[amendment_id].deliberacao = deliberacao

    def get_changes(self, emenda: Emenda, xml_texto_inicial: str) -> List[MudancaEmenda]:
        user_prompt = f"""Aplique a emenda abaixo sobre o XML do texto inicial, retornando as mudanças estruturadas.
        <xml_texto_inicial>
        {xml_texto_inicial}
        </xml_texto_inicial>

        <texto_emenda>
        {emenda.texto}
        </texto_emenda>

        <deliberacao>
        {emenda.deliberacao.justificativa if emenda.deliberacao.status == StatusEmenda.APROVADA_PARCIALMENTE else "Aprovada integralmente"}
        </deliberacao>
        """
        mudancas = self.llm_client.call(SYSTEM_PROMPT_APLICACAO_EMENDAS, user_prompt, response_format=MudancasEmenda)
        return mudancas.mudancas

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
        Aplica a mudança da emenda no XML estruturado, convertendo `change.paragrafos_xhtml`
        em nós LexML via `lexml_parser.parse_articulacao`.
        """
        if not change.id_lexml:
            print("Aviso [Baseline XML]: Emenda sem id_lexml definido.")
            return xml_string

        try:
            tree = etree.fromstring(xml_string.encode("utf-8"), parser=self.xml_parser)

            # Busca o elemento alvo por ID em qualquer nível da árvore (com parâmetro seguro)
            elementos_alvo = tree.xpath("//*[@id=$target_id]", target_id=change.id_lexml)
            if not elementos_alvo:
                print(f"Aviso [Baseline XML]: Elemento com id '{change.id_lexml}' não encontrado.")
                return xml_string

            alvo = elementos_alvo[0]
            pai = alvo.getparent()
            if pai is None:
                print(f"Aviso [Baseline XML]: Elemento '{change.id_lexml}' não possui nó pai.")
                return xml_string

            tag_alvo = etree.QName(alvo).localname

            # 1. Supressão
            if change.tipo == TipoMudancaEmenda.SUPRESSIVA:
                pai.remove(alvo)
                print(f"Sucesso [Baseline]: Dispositivo {tag_alvo} ({change.id_lexml}) suprimido.")

            # 2. Modificação ou Adição
            else:
                if not change.paragrafos_xhtml:
                    print(f"Aviso [Baseline XML]: paragrafos_xhtml vazio para {change.id_lexml}.")
                    return xml_string

                change_xml = self.lexml_parser.parse_articulacao(change.paragrafos_xhtml)
                if not change_xml or not change_xml.strip():
                    print(f"Aviso [Baseline XML]: parse_articulacao retornou vazio para {change.id_lexml}.")
                    return xml_string

                articulacao_fragmento = etree.fromstring(change_xml.encode("utf-8"), parser=self.xml_parser)
                novos_nos = list(articulacao_fragmento)

                if not novos_nos:
                    print(f"Aviso [Baseline XML]: Nenhum nó encontrado no fragmento XML para {change.id_lexml}.")
                    return xml_string

                # Se o pai do alvo não for <Articulacao>, prefixa os IDs do fragmento com o ID do pai
                # (ex: 'art6_cpt' + 'inc6' -> 'art6_cpt_inc6')
                id_pai = pai.get("id")
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

                print(
                    f"Sucesso [Baseline]: Dispositivo {tag_alvo} ({change.id_lexml}) "
                    f"atualizado ({change.tipo.value})."
                )

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