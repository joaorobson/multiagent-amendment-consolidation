import pandas as pd
from experiments.llm import LLMClient, FakeLLMClient
from experiments.ingestion import FileDownloader, TextExtractor
from experiments.baseline.manager import BaselineManager
from models import Proposicao, Emenda, Relatorio
from experiments.utils.datasets import get_pages_with_substitutive
import numpy as np

normas = pd.read_parquet("../data/datasets/normas.parquet")
proposicoes = pd.read_parquet("../data/datasets/proposicoes.parquet")
emendas = pd.read_parquet("../data/datasets/emendas.parquet")
relatorios = pd.read_parquet("../data/datasets/relatorios.parquet")
paginas_com_substitutivo = pd.read_csv("../data/datasets/paginas_com_substitutivo.csv")

dict_paginas = get_pages_with_substitutive(paginas_com_substitutivo)

llm_client = FakeLLMClient(responses={})
baseline_manager = BaselineManager(llm_client, None, None)
downloader = FileDownloader("../data/pdfs")
text_extractor = TextExtractor("../data/pdfs", "../data/txts")


if __name__ == "__main__":
    for idx, row in normas.iterrows():
        proposicoes_norma = proposicoes[proposicoes.urn_norma == row["urn"]]

        for idx, proposicao in proposicoes_norma.iterrows():
            emendas_proposicao_df = emendas[emendas.id_proposicao == proposicao.id]
            emendas_proposicao_df = emendas_proposicao_df.replace({np.nan: None})
            emendas_proposicao = [
                Emenda(**item) for item in emendas_proposicao_df.to_dict(orient="records")
            ]
            status_emendas = baseline_manager.get_amendments_status_dict(emendas_proposicao[:2])

            print(status_emendas)



            relatorios_proposicao = relatorios[relatorios.id_proposicao == proposicao.id]
            for relatorio in relatorios_proposicao.itertuples():
                #downloader.download(relatorio.url_doc, f"{relatorio.id}.pdf")
                #txt_relatorio = text_extractor.extract_text(f"{relatorio.id}.pdf", dict_paginas.get(str(relatorio.id), []))

                extracted_amendments_status = baseline_manager.get_amendments_status("bla bla")
                print(extracted_amendments_status)
                baseline_manager.update_amendments_status(extracted_amendments_status, status_emendas)
                print(status_emendas)
                break

            break
            #downloader.download(proposicao.avulso_inicial_url_doc, f"{proposicao.id}.pdf")
            #txt = text_extractor.extract_text(f"{proposicao.id}.pdf")
            
        
        break