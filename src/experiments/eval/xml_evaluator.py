import re
from lxml import etree
from xmldiff import main, formatting
from xmldiff import actions
from .base_evaluator import BaseEvaluator

class XMLEvaluator(BaseEvaluator):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @staticmethod
    def normalize_text(tree):
        for elem in tree.iter():
            if elem.text:
                elem.text = re.sub(r'\s+', ' ', elem.text).strip()
            if elem.tail:
                elem.tail = re.sub(r'\s+', ' ', elem.tail).strip()
    
    def eval(self, txt, txt_ref):
        parser = etree.XMLParser(remove_blank_text=True)
        
        # 1. Carrega os dois XMLs
        tree_gerado = etree.fromstring(txt.encode('utf-8'), parser=parser)
        tree_ref = etree.fromstring(txt_ref.encode("utf-8"), parser=parser)
        
        # Aplica a normalização de espaços
        XMLEvaluator.normalize_text(tree_gerado)
        XMLEvaluator.normalize_text(tree_ref)
        
        # 2. Converte para BYTES em vez de string decodificada (.encode('utf-8'))
        xml_bytes_gerado = etree.tostring(tree_gerado, encoding='utf-8', xml_declaration=True)
        xml_bytes_ref = etree.tostring(tree_ref, encoding='utf-8', xml_declaration=True)
        
        # 3. Passa os bytes diretamente para o xmldiff
        diff_actions = main.diff_texts(xml_bytes_gerado, xml_bytes_ref)
        
        # 4. Filtra apenas mudanças estruturais reais
        
        classes_estruturais = (
            actions.InsertNode,
            actions.DeleteNode,
            actions.MoveNode,
            actions.RenameNode,
            actions.InsertAttrib,
            actions.DeleteAttrib,
            actions.RenameAttrib
        )
        
        mudancas_relevantes = [
            acao for acao in diff_actions 
            if isinstance(acao, classes_estruturais)
        ]
        
        # Gera relatório visual se houver divergências
        relatorio_visual = None
        if diff_actions:
            relatorio_visual = main.diff_texts(
                xml_bytes_gerado, 
                xml_bytes_ref, 
                formatter=formatting.DiffFormatter()
            )
            
        return {
            "total_acoes": len(diff_actions),
            "total_estrutural": len(mudancas_relevantes),
            "acoes": diff_actions,
            "acoes_estruturais": mudancas_relevantes,
            "relatorio_visual": relatorio_visual
        }