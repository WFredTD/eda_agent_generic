import argparse
from pathlib import Path

import pandas as pd

from agent_utils import Utils
from fluxo import FluxoEDA


def obter_caminho_csv(caminho_entrada: Path) -> Path:
    """
    Determina o caminho do arquivo CSV a ser utilizado.
    Se a entrada for um ZIP, descompacta e encontra o CSV.

    Args:
        caminho_entrada (Path): Caminho para o arquivo CSV ou ZIP.

    Returns:
        Path: O caminho para o arquivo CSV.

    Raises:
        FileNotFoundError: Se o arquivo CSV não for encontrado.
    """
    if caminho_entrada.suffix == ".zip":
        # Cria um diretório de saída com o mesmo nome do arquivo zip, sem a extensão.
        pasta_extraida = Path("outputs") / caminho_entrada.stem
        Utils.verificar_e_descompactar(str(pasta_extraida), str(caminho_entrada))

        # Encontra o arquivo CSV extraído
        arquivos_csv = list(pasta_extraida.glob("*.csv"))
        if not arquivos_csv:
            raise FileNotFoundError(
                "Nenhum arquivo CSV encontrado dentro do arquivo ZIP."
            )

        return arquivos_csv[0]

    elif caminho_entrada.suffix == ".csv":
        if not caminho_entrada.exists():
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_entrada}")
        return caminho_entrada

    else:
        raise ValueError(
            f"Formato de arquivo não suportado: {caminho_entrada.suffix}. Use .csv ou .zip."
        )


def main():
    """
    Função principal para executar o agente de EDA.
    Recebe o caminho do arquivo e a pergunta via linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Agente de EDA genérico para arquivos CSV."
    )
    parser.add_argument(
        "caminho_arquivo",
        type=str,
        help="Caminho para o arquivo CSV ou ZIP a ser analisado.",
    )
    parser.add_argument(
        "pergunta",
        type=str,
        help="A pergunta que o usuário deseja fazer sobre os dados.",
    )
    args = parser.parse_args()

    try:
        caminho_csv = obter_caminho_csv(Path(args.caminho_arquivo))
        pergunta = args.pergunta

        # O DataFrame será carregado dentro do fluxo ou do agente para garantir que ele tenha o contexto do arquivo.
        print(f"Iniciando análise para o arquivo: {caminho_csv}")

        fluxo = FluxoEDA(caminho_csv=caminho_csv)
        resultado = fluxo.kickoff(inputs={"text": pergunta})

        print("\n" + "=" * 50)
        print("✅ Resposta Final do Agente:")
        print("=" * 50)
        print(resultado)

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Erro: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
