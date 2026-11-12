import pandas as pd
from experiments.llm import LLMClient, FakeLLMClient
from experiments.ingestion import FileDownloader, TextExtractor
from experiments.baseline.manager import BaselineManager
from models import Proposicao, Emenda, Relatorio, StatusEmenda
from experiments.utils.datasets import get_pages_with_substitutive
import numpy as np
from experiments.utils import SimilarityRanker
from experiments.eval import EvaluationPipeline, BERTScoreEvaluator, XMLEvaluator
from experiments.lexml.lexml_parser_wrapper import LexMLParserWrapper

normas = pd.read_parquet("../data/datasets/fake/normas.parquet")
proposicoes = pd.read_parquet("../data/datasets/fake/proposicoes.parquet")
emendas = pd.read_parquet("../data/datasets/fake/emendas.parquet")
relatorios = pd.read_parquet("../data/datasets/fake/relatorios.parquet")
paginas_com_substitutivo = pd.read_csv("../data/datasets/paginas_com_substitutivo.csv")

dict_paginas = {} #get_pages_with_substitutive(paginas_com_substitutivo)

llm_client = FakeLLMClient(responses={})
baseline_manager = BaselineManager(llm_client, None, None)
downloader = FileDownloader("../data/pdfs")
text_extractor = TextExtractor("../data/pdfs", "../data/txts")
sim_ranker = SimilarityRanker(None)
lexml_parser = LexMLParserWrapper(jar_path="../data/lexml/lexml-parser-projeto-lei-1.15.8-SNAPSHOT-onejar.jar", java_path="java")
evaluation_pipeline = EvaluationPipeline(lexml_parser, [BERTScoreEvaluator(lexml_parser, "BERTScore"), XMLEvaluator("xmldiff")])
APPLY_RANKING = False
APPLY_PREPROCESSING = False


if __name__ == "__main__":
    for idx, row in normas.iterrows():
        proposicoes_norma = proposicoes[proposicoes.urn_norma == row["urn"]]

        for idx, proposicao in proposicoes_norma.iterrows():
            emendas_proposicao_df = emendas[emendas.id_proposicao == proposicao.id]
            emendas_proposicao_df = emendas_proposicao_df.replace({np.nan: None})
            emendas_proposicao = {item["id"]: Emenda(**item) for item in emendas_proposicao_df.to_dict(orient="records")}

            print("emendas disponiveis:", emendas_proposicao)
            print("="*100)
            relatorios_proposicao = relatorios[relatorios.id_proposicao == proposicao.id]
            relatorios_proposicao.sort_values(by="data_apresentacao", inplace=True)
            for relatorio in relatorios_proposicao.itertuples():
                downloader.download(relatorio.url_doc, f"relatorio-{relatorio.id}.pdf")
                txt_relatorio = text_extractor.extract_text(f"relatorio-{relatorio.id}.pdf", dict_paginas.get(str(relatorio.id), []))

                status_extraido = baseline_manager.get_amendments_status(txt_relatorio)
                print(status_extraido)
                baseline_manager.update_amendments_status(emendas_proposicao, status_extraido)
                break

            downloader.download(proposicao.avulso_inicial_url_doc, f"proposicao-{proposicao.id}.pdf")
            txt_inicial = text_extractor.extract_text(f"proposicao-{proposicao.id}.pdf")

            downloader.download(proposicao.autografo_url_doc, f"autografo-{proposicao.id}.pdf")
            txt_final = text_extractor.extract_text(f"autografo-{proposicao.id}.pdf")

            emendas_para_aplicar = baseline_manager.get_approved_amendments(emendas_proposicao)
            print(emendas_para_aplicar)

            for emenda in emendas_para_aplicar:
                downloader.download(emenda.url_doc, f"emenda-{emenda.id}.pdf")
                emenda.texto = text_extractor.extract_text(f"emenda-{emenda.id}.pdf")

            if APPLY_RANKING:
                first_emenda_id = sorted(emendas_para_aplicar, key=lambda e: e.id)[0].id
                emendas_para_aplicar = sim_ranker.rank_by_similarity({e.id: e.texto for e in emendas_para_aplicar}, first_emenda_id)
            
            changes = {}
            for emenda in emendas_para_aplicar:
                print(f"Aplicando emenda {emenda.id} - {emenda.numero}")
                changes[emenda.id] = baseline_manager.get_changes(emenda, txt_inicial)
            print(changes)

            txt = txt_inicial
            print("-"*100)
            print(txt)
            print("="*100)
            for amendment_id, am_changes in changes.items():
                for change in am_changes:
                    print(change)
                    txt = baseline_manager.apply_amendment_change(change, txt)
                    #print(txt)

            print("texto gerado")
            print(txt)
            print("="*100)

            print("texto final")
            print(txt_final)

            eval_results = evaluation_pipeline.evaluate(txt, txt_final)
            print(eval_results)