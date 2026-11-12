
from typing import Dict, List
from .base_evaluator import BaseEvaluator

class EvaluationPipeline:
    def __init__(self, lexml_parser, evaluators: List[BaseEvaluator]):
        self.lexml_parser = lexml_parser
        self.evaluators = evaluators

    def evaluate(self, texto_gerado: str, texto_referencia: str) -> Dict[str, float]:
        """
        Avalia a similaridade entre o texto gerado e o texto de referência usando BERTScore e xmldiff.
        
        Args:
            texto_gerado (str): O texto gerado pelo sistema.
            texto_referencia (str): O texto de referência (autógrafo).
        
        Returns:
            Dict[str, float]: Um dicionário contendo as métricas de avaliação.
        """


        try:
            # Chama o método passando a string diretamente
            xml_texto_gerado = self.lexml_parser.parse_texto(
                texto=texto_gerado,
                mime_type="text/plain",
                tipo_norma="medida.provisoria",
                autoridade="federal",
                localidade="br",
                numero="123",
                ano="2026",
                output_path="../data/lexml/output.xml",
                opcoes_extras=["--prof-epigrafe-opcional"] # <--- O SEGREDO ESTÁ AQUI
            )

            xml_texto_referencia = self.lexml_parser.parse_texto(
                texto=texto_referencia,
                mime_type="text/plain",
                tipo_norma="medida.provisoria",
                autoridade="federal",
                localidade="br",
                numero="123",
                ano="2026",
                output_path="../data/lexml/output_ref.xml",
                opcoes_extras=["--prof-epigrafe-opcional"] # <--- O SEGREDO ESTÁ AQUI
            )

            with open("../data/lexml/output.xml", "r", encoding="utf-8") as f:
                # 2. Use .strip() para remover qualquer espaço ou quebra de linha inicial invisível
                conteudo_xml = f.read().strip() 

            with open("../data/lexml/output_ref.xml", "r", encoding="utf-8") as f:
                # 2. Use .strip() para remover qualquer espaço ou quebra de linha inicial invisível
                conteudo_xml_ref = f.read().strip() 


            results = {}

            for evaluator in self.evaluators:
                results[evaluator.name]  = evaluator.eval(conteudo_xml, conteudo_xml_ref)

        except Exception as e:
            print(f"Erro: {e}")

        return results