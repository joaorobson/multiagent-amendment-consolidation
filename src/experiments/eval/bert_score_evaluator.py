import torch
from typing import List, Dict, Union
from bert_score import BERTScorer
from .base_evaluator import BaseEvaluator

class BERTScoreEvaluator(BaseEvaluator):
    def __init__(self, lexml_parser, name, model_type: str = "Itau-Unibanco/NorBERTo-large", batch_size: int = 4):
        """
        Inicializa o avaliador carregando o modelo na memória.
        O dispositivo (CPU ou GPU) é detectado automaticamente.
        """
        super().__init__(name)
        self.lexml_parser = lexml_parser
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.batch_size = batch_size
        
        print(f"Carregando {model_type} no dispositivo: {self.device}...")
        self.scorer = BERTScorer(
            model_type=model_type,
            device=self.device,
            lang="pt",
            num_layers=28
            # Se usar um modelo que não é nativo em pt-br, pode-se passar lang="pt"
            # Como o NorBERTo é nativo, omitimos ou gerenciamos internamente pela biblioteca
        )

    def get_chunks(self, txt):
        return self.lexml_parser.extrair_artigos(txt)

    def eval(
            self, 
            txt: str, 
            txt_ref: str
        ) -> Dict[str, Union[float, List[Dict[str, float]]]]:
        """
        Avalia um texto único ou um lote de textos gerados em relação às referências.
        Identifica automaticamente o tipo de entrada (str vs List[str]).
        """

        txts = self.get_chunks(txt)
        txts_ref = self.get_chunks(txt_ref)

        # Validação de tamanho para listas
        if len(txts) != len(txts_ref):
            raise ValueError("As listas de textos gerados e de referência precisam ter o mesmo tamanho.")
            
        # Executa o BERTScore (suporta lotes eficientemente)
        P, R, F1 = self.scorer.score(txts, txts_ref, batch_size=getattr(self, 'batch_size', 32))
            
        # Se foi passado uma lista, retorna as médias e os scores individuais (batch)
        scores_individuais = [
            {
                "Precisao": round(p.item(), 4), 
                "Recall": round(r.item(), 4), 
                "F1_Score": round(f.item(), 4)
            }
            for p, r, f in zip(P, R, F1)
        ]
        
        return {
            "Precisao_Media": round(P.mean().item(), 4),
            "Recall_Medio": round(R.mean().item(), 4),
            "F1_Score_Medio": round(F1.mean().item(), 4),
            "Scores_Individuais": scores_individuais
        }