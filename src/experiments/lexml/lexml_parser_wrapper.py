import subprocess
import re
from typing import List, Optional, Union
import os
import tempfile
import xml.etree.ElementTree as ET


class LexMLParserWrapper:
    """Classe em Python para encapsular a execução do lexml-parser-projeto-lei (JAR)."""

    def __init__(self, jar_path: str, java_path: str = "java"):
        self.jar_path = jar_path
        self.java_path = java_path

    def _sanitizar_texto_lexml(self, texto: str) -> str:
        """
        Limpa o texto para garantir conformidade com as Regex do LexML Parser
        e contorna o bug de agrupamento reverso (toPars) no XHTMLProcessor.scala.
        """
        if not texto:
            return texto

        texto = texto.replace("–", "-").replace("—", "-")
        texto = texto.replace("°", "º")

        linhas_validas = [linha for linha in texto.splitlines() if linha.strip()]
        texto = "\n\n".join(linhas_validas)

        texto = re.sub(r'^([IVXLCDM]+)\s*-\s*', r'\1 - ', texto, flags=re.MULTILINE)

        return texto

    def _montar_xhtml_articulacao(self, texto: Union[str, List[str]]) -> str:
        """Converte texto plano (ou lista de parágrafos) para <root><p>...</p></root>."""
        if isinstance(texto, list):
            linhas = [linha.strip() for linha in texto if linha and linha.strip()]
        else:
            texto_limpo = self._sanitizar_texto_lexml(texto)
            linhas = [linha.strip() for linha in texto_limpo.splitlines() if linha.strip()]

        root = ET.Element("root")
        for linha in linhas:
            p = ET.SubElement(root, "p")
            p.text = linha

        return ET.tostring(root, encoding="unicode")

    def _executar(self, args: List[str]) -> subprocess.CompletedProcess:
        """Método interno para executar o comando via subprocess."""
        comando = [self.java_path, "-Dfile.encoding=UTF-8", "-jar", self.jar_path] + args
        try:
            return subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
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
        texto: Optional[Union[str, List[str]]] = None,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        linker: Optional[str] = None,
    ) -> str:
        """Faz o parse apenas da articulação (comando parseArticulacao)."""
        tmp_in_path = None
        tmp_out_path = None
        try:
            if texto is not None:
                conteudo_xml = (
                    texto
                    if isinstance(texto, str) and texto.lstrip().startswith("<")
                    else self._montar_xhtml_articulacao(texto)
                )
                with tempfile.NamedTemporaryFile(
                    delete=False, mode="w", encoding="utf-8", suffix=".xml"
                ) as tmp_in:
                    tmp_in.write(conteudo_xml)
                    tmp_in_path = tmp_in.name
                input_path = tmp_in_path

            # Se output_path não foi informado, grava em arquivo temporário para isolar dos logs do Pekko
            if not output_path:
                with tempfile.NamedTemporaryFile(
                    delete=False, mode="w", encoding="utf-8", suffix=".xml"
                ) as tmp_out:
                    tmp_out_path = tmp_out.name
                destino_saida = tmp_out_path
            else:
                destino_saida = output_path

            args = ["parseArticulacao"]
            if input_path:
                args.extend(["-i", input_path])
            args.extend(["-o", destino_saida])
            if linker:
                args.extend(["--linker", linker])

            resultado = self._executar(args)
            if resultado.returncode != 0:
                raise RuntimeError(f"Erro no parseArticulacao: {resultado.stderr}")

            with open(destino_saida, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            for path in (tmp_in_path, tmp_out_path):
                if path and os.path.exists(path):
                    os.remove(path)

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
        texto = self._sanitizar_texto_lexml(texto)

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8", suffix=".txt"
        ) as tmp_in:
            tmp_in.write(texto)
            tmp_in_path = tmp_in.name

        tmp_out_path = None
        output_path = kwargs.get("output_path")
        if not output_path:
            with tempfile.NamedTemporaryFile(
                delete=False, mode="w", encoding="utf-8", suffix=".xml"
            ) as tmp_out:
                tmp_out_path = tmp_out.name
            destino_saida = tmp_out_path
        else:
            destino_saida = output_path

        try:
            args = ["parse", "-m", mime_type, "-i", tmp_in_path, "-o", destino_saida]

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

            resultado = self._executar(args)
            if resultado.returncode != 0:
                raise RuntimeError(f"Erro no parse de texto: {resultado.stderr}")

            with open(destino_saida, "r", encoding="utf-8") as f:
                return f.read()

        finally:
            for path in (tmp_in_path, tmp_out_path):
                if path and os.path.exists(path):
                    os.remove(path)

    @staticmethod
    def extrair_artigos_por_id(xml: str) -> dict[str, str]:
        """Retorna um dicionário {id_lexml: texto_artigo} mantendo a ordem do documento."""
        inicio = xml.find("<")
        if inicio > 0:
            xml = xml[inicio:]

        root = ET.fromstring(xml)
        ns = {"lex": "http://www.lexml.gov.br/1.0"}
        artigos: dict[str, str] = {}

        for idx, artigo in enumerate(root.findall(".//lex:Articulacao//lex:Artigo", ns)):
            art_id = artigo.get("id") or f"sem_id_{idx}"
            texto = " ".join(
                t.strip()
                for t in artigo.itertext()
                if t.strip()
            )
            artigos[art_id] = texto

        return artigos

    @classmethod
    def alinhar_artigos(cls, xml_gerado: str, xml_ref: str) -> tuple[list[str], list[str]]:
        """
        Alinha os artigos pela união ordenada dos IDs LexML.
        Preenche com string vazia '' quando um artigo existe em apenas um dos XMLs,
        permitindo que o BERTScore penalize omissões (Recall) e inserções indevidas (Precision).
        """
        mapa_gerado = cls.extrair_artigos_por_id(xml_gerado)
        mapa_ref = cls.extrair_artigos_por_id(xml_ref)

        # União preservando a ordem do gabarito oficial (xml_ref),
        # seguida de eventuais artigos extras gerados que não existem no gabarito
        todos_ids = list(dict.fromkeys(list(mapa_ref.keys()) + list(mapa_gerado.keys())))

        txts_gerados = [mapa_gerado.get(art_id, "") for art_id in todos_ids]
        txts_ref = [mapa_ref.get(art_id, "") for art_id in todos_ids]

        return txts_gerados, txts_ref