from typing import Dict

class SimilarityRanker:
    def __init__(self, embedding_client):
        self.embedding_client = embedding_client
    
    def generate_embeddings(self):
        ...

    def rank_by_similarity(self, docs: Dict[int, str], first_doc: int) -> Dict[int, str]:
        return docs
        