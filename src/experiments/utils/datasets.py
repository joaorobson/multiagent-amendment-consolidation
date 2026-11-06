import pandas as pd

def get_pages_with_substitutive(df):
    ix_cols = [col for col in df.columns if col.startswith("ix")]

    # Dicionário que vai armazenar: { "id_pdf": [[inicio, fim], ...] }
    dict_paginas = {}

    for _, row in df.iterrows():
        id_agrupado = row["id_agrupado"]
        if pd.isna(id_agrupado):
            continue
        
        # Separa os IDs caso venham separados por vírgula
        ids_individuais = [i.strip() for i in str(id_agrupado).split(",") if i.strip()]
        
        # Coleta os valores de ix válidos para esta linha
        valores_ix = []
        sem_remocao = False
        
        for col in ix_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip()
                
                # Se encontrar '-', significa que não há páginas para remover nesta linha
                if val_str == "-":
                    sem_remocao = True
                    break
                    
                try:
                    valores_ix.append(int(val_str))
                except ValueError:
                    pass
                    
        # Se encontrou '-', a lista de ranges fica vazia
        ranges = []
        if not sem_remocao:
            for i in range(0, len(valores_ix), 2):
                if i + 1 < len(valores_ix):
                    ranges.append([valores_ix[i], valores_ix[i+1]])
                
        # Popula o dicionário para cada ID encontrado na linha
        for pdf_id in ids_individuais:
            if pdf_id not in dict_paginas:
                dict_paginas[pdf_id] = []
            
            # Se houver ranges, adiciona. Se for vazio, não adiciona nada.
            if ranges:
                dict_paginas[pdf_id].extend(ranges)

    print(f"Dicionário criado! Total de PDFs mapeados: {len(dict_paginas)}")
    
    return dict_paginas
