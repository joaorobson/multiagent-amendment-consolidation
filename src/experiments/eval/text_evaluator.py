
from typing import Dict


class TextEvaluator:
    def __init__(self, bert_score_evaluator, lexml_parser):
        self.bert_score_evaluator = bert_score_evaluator
        self.lexml_parser = lexml_parser

    def evaluate_autografo(self, texto_gerado: str, texto_referencia: str) -> Dict[str, float]:
        """
        Avalia a similaridade entre o texto gerado e o texto de referência usando BERTScore.
        
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


            artigos_gerado = self.lexml_parser.extrair_artigos(conteudo_xml)
            artigos_referencia = self.lexml_parser.extrair_artigos(conteudo_xml_ref)
            print(artigos_gerado)
            print(artigos_referencia)

            resultados = self.bert_score_evaluator.avaliar_lote(textos_gerados=artigos_gerado, textos_referencia=artigos_referencia)
            print(resultados)
        except Exception as e:
            print(f"Erro: {e}")

        pass