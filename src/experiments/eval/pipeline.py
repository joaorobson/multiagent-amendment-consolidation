
from typing import Dict, List
from .base_evaluator import BaseEvaluator

class EvaluationPipeline:
    def __init__(self, lexml_parser, evaluators: List[BaseEvaluator]):
        self.lexml_parser = lexml_parser
        self.evaluators = evaluators

    def evaluate(self, xml: str, xml_ref: str) -> Dict[str, float]:
        """
        Avalia a similaridade entre o texto gerado e o texto de referência usando BERTScore e xmldiff.
        
        Args:
            texto_gerado (str): O texto gerado pelo sistema.
            texto_referencia (str): O texto de referência (autógrafo).
        
        Returns:
            Dict[str, float]: Um dicionário contendo as métricas de avaliação.
        """


        results = {}

        for evaluator in self.evaluators:
            results[evaluator.name]  = evaluator.eval(xml, xml_ref)



        return results