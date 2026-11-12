from abc import ABC, abstractmethod
from typing import List, Dict

class BaseEvaluator(ABC):
    def __init__(self, name: str) -> None:
        self.name = name
    
    @abstractmethod
    def eval(self, txt: str, txt_ref: str) -> dict:
        """
        Avalia o texto gerado (txt) em relação ao texto de referência (txt_ref)
        e retorna uma pontuação (score).
        """
        pass