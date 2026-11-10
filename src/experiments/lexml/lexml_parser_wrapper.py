import subprocess
import re
from typing import List, Optional
import os
import sys
import tempfile
import xml.etree.ElementTree as ET


class LexMLParserWrapper:
    """Classe em Python para encapsular a execução do lexml-parser-projeto-lei (JAR)."""

    def __init__(self, jar_path: str, java_path: str = "java"):
        """Inicializa o wrapper do LexML Parser.

        :path: Caminho para o arquivo .jar compilado (ex:
        'target/lexml-parser-projeto-lei-1.0.0-onejar.jar')
        :param java_path: Caminho para o executável java (default: 'java')
        """
        self.jar_path = jar_path
        self.java_path = java_path

    def _sanitizar_texto_lexml(self, texto: str) -> str:
        """
        Limpa o texto para garantir conformidade com as Regex do LexML Parser 
        e contorna o bug de agrupamento reverso (toPars) no XHTMLProcessor.scala.
        """
        if not texto:
            return texto

        # 1. Troca travessões (en-dash e em-dash) por hífen simples
        texto = texto.replace("–", "-").replace("—", "-")
        
        # 2. Troca o símbolo de grau (°) pelo ordinal correto (º)
        texto = texto.replace("°", "º")
        
        # 3. Força uma quebra de linha extra entre as linhas com conteúdo.
        # Isso isola cada parágrafo em um bloco próprio, impedindo o bug
        # de inversão de linhas (reverse) no parser do texto plano.
        linhas_validas = [linha for linha in texto.splitlines() if linha.strip()]
        texto = "\n\n".join(linhas_validas)
        
        # 4. Garante espaçamento rigoroso nos incisos (Ex: "I- " vira "I - ")
        # Regex atua no início de linha capturando numerais romanos
        texto = re.sub(r'^([IVXLCDM]+)\s*-\s*', r'\1 - ', texto, flags=re.MULTILINE)
        
        return texto

    def _executar(self, args: List[str]) -> subprocess.CompletedProcess:
        """Método interno para executar o comando via subprocess."""
        comando = [self.java_path, "-jar", self.jar_path] + args
        try:
            resultado = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                check=False,
            )
            return resultado
        except Exception as e:
            raise RuntimeError(f"Erro ao executar o comando Java: {e}")

    def dump_profiles(self) -> str:
        """Mostra os perfis de normas presentes no parser (comando dumpProfiles)."""
        resultado = self._executar(["dumpProfiles"])
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no dumpProfiles: {resultado.stderr}")
        return resultado.stdout

    def parse_articulacao(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        linker: Optional[str] = None,
    ) -> str:
        """Faz o parse apenas da articulação (comando parseArticulacao)."""
        args = ["parseArticulacao"]
        if input_path:
            args.extend(["-i", input_path])
        if output_path:
            args.extend(["-o", output_path])
        if linker:
            args.extend(["--linker", linker])

        resultado = self._executar(args)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no parseArticulacao: {resultado.stderr}")
        return resultado.stdout

    def parse(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        tipo_norma: Optional[str] = None,
        autoridade: Optional[str] = None,
        localidade: Optional[str] = None,
        numero: Optional[str] = None,
        ano: Optional[str] = None,
        data: Optional[str] = None,
        write_errors_to_file: Optional[str] = None,
        info: bool = False,
        complemento: Optional[str] = None,
        data_evento: Optional[str] = None,
        tipo_evento: Optional[str] = None,
        timestamp_evento: Optional[str] = None,
        linker: Optional[str] = None,
        opcoes_extras: Optional[List[str]] = None,
    ) -> str:
        """Executa o comando principal 'parse' com as opções suportadas."""
        args = ["parse"]

        if mime_type:
            args.extend(["-m", mime_type])
        if input_path:
            args.extend(["-i", input_path])
        if output_path:
            args.extend(["-o", output_path])
        if write_errors_to_file:
            args.extend(["--write-errors-to-file", write_errors_to_file])
        if info:
            args.append("--info")
        if tipo_norma:
            args.extend(["-t", tipo_norma])
        if autoridade:
            args.extend(["-a", autoridade])
        if localidade:
            args.extend(["-l", localidade])
        if numero:
            args.extend(["-n", str(numero)])
        if complemento:
            args.extend(["--complemento", complemento])
        if ano:
            args.extend(["--ano", str(ano)])
        if data:
            args.extend(["--data", data])
        if data_evento:
            args.extend(["--data-evento", data_evento])
        if tipo_evento:
            args.extend(["--tipo-evento", tipo_evento])
        if timestamp_evento:
            args.extend(["--timestamp-evento", timestamp_evento])
        if linker:
            args.extend(["--linker", linker])

        if opcoes_extras:
            args.extend(opcoes_extras)

        resultado = self._executar(args)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro no parse: {resultado.stderr}")
        return resultado.stdout

    def parse_texto(self, texto: str, mime_type: str = "text/plain", **kwargs) -> str:
        """Executa o comando 'parse' recebendo o conteúdo do texto diretamente da memória."""
        
        # 1. Sanitiza o texto
        texto = self._sanitizar_texto_lexml(texto)

        # 2. Cria um arquivo temporário e escreve o texto nele
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as tmp:
            tmp.write(texto)
            tmp_path = tmp.name

        try:
            # 3. Prepara os argumentos
            args = ["parse"]
            args.extend(["-m", mime_type])
            args.extend(["-i", tmp_path]) # <--- PASSA O ARQUIVO TEMPORÁRIO AQUI

            # Repassa os demais argumentos opcionais, exceto input_path e output_path (pois queremos a saída no stdout)
            if kwargs.get("mime_type"):
                args.extend(["-m", kwargs["mime_type"]])
            if kwargs.get("output_path"):
                args.extend(["-o", kwargs["output_path"]])
            if kwargs.get("write_errors_to_file"):
                args.extend(["--write-errors-to-file", kwargs["write_errors_to_file"]])
            if kwargs.get("info"):
                args.append("--info")
            if kwargs.get("tipo_norma"):
                args.extend(["-t", kwargs["tipo_norma"]])
            if kwargs.get("autoridade"):
                args.extend(["-a", kwargs["autoridade"]])
            if kwargs.get("localidade"):
                args.extend(["-l", kwargs["localidade"]])
            if kwargs.get("numero"):
                args.extend(["-n", str(kwargs["numero"])])
            if kwargs.get("complemento"):
                args.extend(["--complemento", kwargs["complemento"]])
            if kwargs.get("ano"):
                args.extend(["--ano", str(kwargs["ano"])])
            if kwargs.get("data"):
                args.extend(["--data", kwargs["data"]])
            if kwargs.get("data_evento"):
                args.extend(["--data-evento", kwargs["data_evento"]])
            if kwargs.get("tipo_evento"):
                args.extend(["--tipo-evento", kwargs["tipo_evento"]])
            if kwargs.get("timestamp_evento"):
                args.extend(["--timestamp-evento", kwargs["timestamp_evento"]])
            if kwargs.get("linker"):
                args.extend(["--linker", kwargs["linker"]])
            if kwargs.get("opcoes_extras"):
                args.extend(kwargs["opcoes_extras"])

            comando = [self.java_path, "-jar", self.jar_path] + args
            
            # 4. Executa o comando (sem usar o input=texto do subprocess)
            resultado = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            
            if resultado.returncode != 0:
                raise RuntimeError(f"Erro no parse de texto: {resultado.stderr}")
                
            return resultado.stdout

        finally:
            # 5. Garante que o arquivo temporário será apagado mesmo se der erro
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def extrair_artigos(xml: str) -> list[str]:
        root = ET.fromstring(xml)

        ns = {"lex": "http://www.lexml.gov.br/1.0"}

        artigos = []

        for artigo in root.findall(".//lex:Articulacao/lex:Artigo", ns):
            texto = " ".join(
                texto.strip()
                for texto in artigo.itertext()
                if texto.strip()
            )

            artigos.append(texto)

        return artigos