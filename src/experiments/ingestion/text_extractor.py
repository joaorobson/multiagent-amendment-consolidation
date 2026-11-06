import fitz
import os
import json
import pytesseract

from PIL import Image
from typing import List


class TextExtractor:
    def __init__(self, pdfs_path: str, txts_path: str, lang: str = "por", document_root: str = "data") -> None:
        self.pdfs_path = pdfs_path
        self.txts_path = txts_path
        self.lang = lang
        self.document_root = document_root

        print(f"[INIT] TextExtractor inicializado")
        print(f"[INIT] pdfs_path={self.pdfs_path}")
        print(f"[INIT] lang={self.lang}")
        print(f"[INIT] document_root={self.document_root}")

    def store_txt(self, content: str, filename: str) -> None:
        if not os.path.exists(self.txts_path):
            os.makedirs(self.txts_path)
            print(f"[STORE] Pasta criada: {self.txts_path}")

        filepath = os.path.join(self.txts_path, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[STORE] Arquivo salvo: {filepath}")

    def _ls_to_local_path(self, ls_path):
        prefix = "/data/local-files/?d="
        relative = ls_path.replace(prefix, "")
        local_path = os.path.join(self.document_root, relative)

        print(f"[PATH] LS -> Local")
        print(f"       origem: {ls_path}")
        print(f"       local : {local_path}")

        return local_path

    def extract_page_with_ocr(self, page, zoom=3):
        print(f"[OCR] Renderizando página com zoom={zoom}")

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        print(f"[OCR] Aplicando pytesseract...")

        text = pytesseract.image_to_string(img, lang=self.lang)

        print(f"[OCR] Extração concluída ({len(text)} chars)")

        return text

    def extract_text(self, filename: str, pages_to_remove: List[List[int]] = None) -> str:
        """
        Extrai o texto do PDF, permitindo excluir páginas por intervalos.
        Exemplo: pages_to_remove = [[3, 5], [8, 9]] (indexado a partir de 1).
        """
        # Define o nome e o caminho esperado do arquivo de texto
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_filepath = os.path.join(self.txts_path, txt_filename)

        # Verifica se o arquivo txt já existe
        if os.path.exists(txt_filepath):
            print(f"[CACHE] O arquivo já existe, pulando extração: {txt_filepath}")
            with open(txt_filepath, "r", encoding="utf-8") as f:
                return f.read()

        print(f"[PDF] Iniciando processamento de PDFs")

        filepath = os.path.join(self.pdfs_path, filename)

        if not filepath.lower().endswith(".pdf"):
            return None

        print(f"\n[PDF] Processando: {filename}")

        doc = fitz.open(filepath)

        # -------------------------------------------------------------
        # VALIDAÇÃO E LÓGICA DE EXCLUSÃO DE PÁGINAS
        # -------------------------------------------------------------
        if pages_to_remove:
            if not isinstance(pages_to_remove, list):
                raise TypeError("O parâmetro 'pages_to_remove' deve ser uma lista.")
            
            indices_para_remover = set()
            for item in pages_to_remove:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise ValueError(f"Cada intervalo deve ser uma lista/tupla com exatamente 2 membros. Inválido: {item}")
                
                inicio, fim = item
                for p in range(inicio, fim + 1):
                    indices_para_remover.add(p - 1)  # Converte para índice 0

            indices_ordenados = sorted(list(indices_para_remover), reverse=True)
            
            print(f"[PDF] Removendo páginas (índices 0-based): {indices_ordenados}")
            for idx in indices_ordenados:
                if 0 <= idx < len(doc):
                    doc.delete_page(idx)

        print(f"[PDF] Total páginas (após remoções): {len(doc)}")

        if len(doc) == 0:
            print("[PDF] Aviso: O documento ficou sem páginas após a remoção.")
            doc.close()
            return ""

        first_page_text = doc[0].get_text().strip()

        use_ocr = len(first_page_text) < 100

        print(f"[PDF] OCR necessário? {use_ocr}")

        all_text = ""

        for page_num, page in enumerate(doc):
            print(f"[PDF] Página {page_num}")

            if use_ocr:
                text = self.extract_page_with_ocr(page)
            else:
                text = page.get_text()
                print(f"[PDF] Texto nativo extraído ({len(text)} chars)")

            all_text += text + "\n"

        # Salva o arquivo de texto completo após processar todas as páginas
        self.store_txt(all_text, txt_filename)
             
        doc.close()
        return all_text