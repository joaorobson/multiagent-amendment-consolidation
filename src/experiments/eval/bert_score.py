import torch
from typing import List, Dict, Union
from bert_score import BERTScorer

class BERTScoreEvaluator:
    def __init__(self, model_type: str = "Itau-Unibanco/NorBERTo-large", batch_size: int = 4):
        """
        Inicializa o avaliador carregando o modelo na memória.
        O dispositivo (CPU ou GPU) é detectado automaticamente.
        """
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

    def avaliar_par(self, texto_gerado: str, texto_referencia: str) -> Dict[str, float]:
        """
        Avalia um único par de textos.
        Útil para debugar as saídas de uma deliberação ou aplicação específica de emenda.
        """
        # O BERTScore espera receber listas de strings
        P, R, F1 = self.scorer.score([texto_gerado], [texto_referencia])
        
        return {
            "Precisao": round(P.item(), 4),
            "Recall": round(R.item(), 4),
            "F1_Score": round(F1.item(), 4)
        }

    def avaliar_lote(self, textos_gerados: List[str], textos_referencia: List[str]) -> Dict[str, Union[float, List[Dict[str, float]]]]:
        """
        Avalia múltiplos textos simultaneamente.
        Ideal para o dataset de benchmark final comparando todos os autógrafos gerados.
        """
        if len(textos_gerados) != len(textos_referencia):
            raise ValueError("As listas de textos gerados e de referência precisam ter o mesmo tamanho.")
            
        P, R, F1 = self.scorer.score(textos_gerados, textos_referencia, batch_size=self.batch_size)
        
        scores_individuais = [
            {
                "Precisao": round(p.item(), 4), 
                "Recall": round(r.item(), 4), 
                "F1_Score": round(f.item(), 4)
            }
            for p, r, f in zip(P, R, F1)
        ]
        print(scores_individuais)
        return {
            "Precisao_Media": round(P.mean().item(), 4),
            "Recall_Medio": round(R.mean().item(), 4),
            "F1_Score_Medio": round(F1.mean().item(), 4),
            "Scores_Individuais": scores_individuais
        }