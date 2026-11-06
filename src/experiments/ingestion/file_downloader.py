from pathlib import Path
from urllib.request import Request, urlopen


class FileDownloader:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, filename: str | None = None) -> Path:
        if filename is None:
            filename = Path(url.split("?", 1)[0]).name or "document.pdf"

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        output_path = self.output_dir / filename

        # Verifica se o arquivo já existe localmente
        if output_path.exists():
            print(f"[CACHE] O arquivo já existe, pulando download: {output_path}")
            return output_path

        print(f"[DOWNLOAD] Baixando: {url}")
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        with urlopen(request) as response:
            output_path.write_bytes(response.read())

        print(f"[DOWNLOAD] Salvo em: {output_path}")
        return output_path