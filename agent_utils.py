import os
import zipfile
from pathlib import Path


class Utils:
    """
    Classe de utilidades para manipulação de arquivos no projeto.
    """

    @staticmethod
    def descompactar_arquivo_zip(caminho_zip: str, destino: str = None) -> Path:
        """
        Descompacta um arquivo .zip no diretório de destino informado.
        Se o destino não for especificado, descompacta no mesmo diretório do arquivo zip.

        Args:
            caminho_zip (str): Caminho completo para o arquivo .zip.
            destino (str, optional): Caminho do diretório onde os arquivos serão extraídos.
                                     Defaults to None.

        Returns:
            Path: O caminho para o diretório onde os arquivos foram extraídos.

        Raises:
            FileNotFoundError: Se o arquivo ZIP for inválido ou não encontrado.
        """
        caminho_zip = Path(caminho_zip)

        if not caminho_zip.exists() or not zipfile.is_zipfile(caminho_zip):
            raise FileNotFoundError(
                f"Arquivo ZIP inválido ou não encontrado: {caminho_zip}"
            )

        destino = Path(destino) if destino else caminho_zip.parent / caminho_zip.stem
        destino.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
            zip_ref.extractall(destino)
            print(f"✅ Arquivos extraídos para: {destino.resolve()}")

        return destino

    @staticmethod
    def verificar_e_descompactar(caminho_pasta: str, caminho_zip: str) -> Path:
        """
        Verifica se a pasta de destino está vazia. Se estiver, descompacta o .zip nela.

        Args:
            caminho_pasta (str): O caminho do diretório de destino.
            caminho_zip (str): O caminho completo para o arquivo .zip.

        Returns:
            Path: O caminho para o diretório com os arquivos extraídos.
        """
        pasta = Path(caminho_pasta)

        if not pasta.exists():
            print(f"📁 Pasta não existe, criando: {pasta}")
            pasta.mkdir(parents=True)

        arquivos = list(pasta.iterdir())

        if arquivos:
            print(
                f"📂 Pasta '{pasta}' já contém arquivos. Nenhuma ação de descompactação necessária."
            )
            return pasta
        else:
            print(f"⚠️ Pasta '{pasta}' está vazia. Iniciando descompactação...")
            try:
                return Utils.descompactar_arquivo_zip(caminho_zip, caminho_pasta)
            except Exception as e:
                print(f"❌ Falha ao descompactar: {e}")
                raise
