import pandas as pd
from experiments.llm import LLMClient
from experiments.ingestion import FileDownloader, TextExtractor

normas = pd.read_parquet("../data/datasets/normas.parquet")
proposicoes = pd.read_parquet("../data/datasets/proposicoes.parquet")
emendas = pd.read_parquet("../data/datasets/emendas.parquet")
relatorios = pd.read_parquet("../data/datasets/relatorios.parquet")

llm_client = LLMClient()
downloader = FileDownloader("../data/pdfs")
text_extractor = TextExtractor("../data/pdfs", "../data/txts")

if __name__ == "__main__":
    for idx, row in normas.iterrows():
        proposicoes_norma = proposicoes[proposicoes.urn_norma == row["urn"]]

        for idx, proposicao in proposicoes_norma.iterrows():
            print(proposicao.url_doc)
            downloader.download(proposicao.url_doc, f"{proposicao.id}.pdf")
            txt = text_extractor.extract_text(f"{proposicao.id}.pdf")

            emendas_proposicao = emendas[emendas.id_proposicao == proposicao.id]
            relatorios_proposicao = relatorios[relatorios.id_proposicao == proposicao.id]
            
        break