import pandas as pd
from experiments.llm import LLMClient

normas = pd.read_parquet("../data/normas.parquet")

llm_client = LLMClient()


if __name__ == "__main__":
    for idx, row in normas.iterrows():
        print(row)
        break