import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class QueryCSVGenerico(BaseTool):
    """
    Ferramenta para executar código Python de consulta a um DataFrame.
    Esta ferramenta opera em um DataFrame de pandas que é injetado no contexto.
    """

    name: str = "Ferramenta de execucao de codigo de consulta a um CSV"
    description: str = (
        "Executa e retorna dados de uma consulta Python em um DataFrame (df). "
        "A entrada deve ser um código Python completo para ser executado. "
        "O DataFrame já está carregado na variável 'df'."
    )
    # Atributo para armazenar o DataFrame
    df: pd.DataFrame = None

    def _run(self, codigo_python: str) -> str:
        # A ferramenta não precisa mais do file_path, pois o df será injetado
        contexto = {"df": self.df, "pd": pd, "np": np}
        try:
            # --- CORREÇÃO: Forçar a atribuição da última expressão a 'resultado' ---
            linhas = codigo_python.strip().split("\n")
            ultima_linha = linhas[-1].strip()

            # Verificar se a última linha não é uma atribuição (contém '=') e não é um import/def
            if "=" not in ultima_linha and not ultima_linha.startswith(
                ("import", "def", "class")
            ):
                # Se for uma expressão (ex: df['col'].describe()), a atribuímos a 'resultado'
                codigo_python = "\n".join(linhas[:-1]) + f"\nresultado = {ultima_linha}"
            # -----------------------------------------------------------------------

            # Executar o código fornecido pelo agente
            exec(codigo_python, contexto)

            # Tentar obter o resultado de uma variável 'resultado'
            if "resultado" in contexto:
                resultado_final = contexto["resultado"]
                # Se for um DataFrame ou Series, converte para string
                if isinstance(resultado_final, (pd.DataFrame, pd.Series)):
                    # Limitar o output para não estourar o buffer de tokens
                    return resultado_final.to_string(
                        index=True, max_rows=50
                    )  # Mudança: 'index=True' para Series (como describe)
                return str(resultado_final)

            return f"[AVISO] Código executado, mas nenhuma variável 'resultado' foi definida. Código: {codigo_python}"
        except Exception as e:
            return f"[ERRO] Falha ao executar a consulta: {e}"


class PlotarGraficoTool(BaseTool):
    """
    Ferramenta para criar e salvar um gráfico a partir de um DataFrame.
    """

    name: str = "Ferramenta de geracao de grafico"
    description: str = (
        "Cria um gráfico a partir do DataFrame (df) e salva como uma imagem. "
        "A entrada deve ser um dicionário com `tipo_grafico`, `colunas` e `titulo`. "
        "Tipos de gráficos disponíveis: histograma, dispersao, boxplot, barras e multiplos_histogramas."
    )

    class PlotarGraficoSchema(BaseModel):
        tipo_grafico: str = Field(
            ...,
            description="O tipo de gráfico a ser gerado. Escolha entre: 'histograma', 'dispersao', 'boxplot', 'barras', 'multiplos_histogramas'.",
        )
        colunas: list[str] = Field(
            ...,
            description="Uma lista de strings com os nomes das colunas do DataFrame a serem utilizadas no gráfico.",
        )
        titulo: str = Field(
            None,
            description="O título do gráfico. Se não fornecido, será gerado automaticamente.",
        )

    # Atribua o esquema de validação
    args_schema = PlotarGraficoSchema

    # Atributo para armazenar o DataFrame
    df: pd.DataFrame = None

    # Mude a assinatura do método _run para aceitar argumentos separados
    def _run(
        self, tipo_grafico: str, colunas: list[str], titulo: str = "Gráfico"
    ) -> str:
        """
        Gera um gráfico com base nos dados do DataFrame.

        Args:
            tipo_grafico (str): Tipo do gráfico.
            colunas (list[str]): Nomes das colunas a serem usadas.
            titulo (str, optional): Título do gráfico. Defaults to 'Gráfico'.

        Returns:
            str: O caminho do arquivo de imagem gerado ou uma mensagem de erro.
        """

        try:
            # Configurar matplotlib para não usar display E não mostrar gráficos
            import matplotlib

            matplotlib.use("Agg")  # Backend não-interativo
            plt.ioff()  # Desligar modo interativo

            # Limpar qualquer plot anterior
            plt.clf()
            plt.close("all")

            # Criar diretório outputs se não existir
            outputs_dir = Path("outputs")
            outputs_dir.mkdir(exist_ok=True)

            if tipo_grafico == "histograma":
                if not colunas:
                    return "[ERRO] Colunas não especificadas para o histograma."

                plt.figure(figsize=(10, 6))
                coluna = colunas[0]

                if coluna not in self.df.columns:
                    return f"[ERRO] Coluna '{coluna}' não encontrada no DataFrame."

                plt.hist(
                    self.df[coluna].dropna(),
                    bins=30,
                    alpha=0.7,
                    color="skyblue",
                    edgecolor="black",
                )
                plt.title(titulo)
                plt.xlabel(coluna)
                plt.ylabel("Frequência")
                plt.grid(True, alpha=0.3)

            elif tipo_grafico == "multiplos_histogramas":

                # --- LÓGICA CORRIGIDA PARA USAR COLUNAS ESPECÍFICAS SE FOREM FORNECIDAS ---
                if colunas and len(colunas) > 0:
                    # Se colunas forem fornecidas pelo agente, use APENAS elas (e filtre as válidas).
                    # A LLM tentou enviar LotArea, YearBuilt e SalePrice. Vamos honrar esse pedido.
                    colunas_a_plotar = [
                        col for col in colunas if col in self.df.columns
                    ]
                else:
                    # Se não houver colunas (pedido genérico 'gere histogramas'), use TODAS as numéricas.
                    colunas_a_plotar = self.df.select_dtypes(
                        include=[np.number]
                    ).columns.tolist()

                # --- MANTER RESTRIÇÃO DE TAMANHO (MÁXIMO DE 30) ---
                if len(colunas_a_plotar) > 30:
                    colunas_a_plotar = colunas_a_plotar[:30]
                    print(
                        f"⚠️ Limitando a {len(colunas_a_plotar)} colunas devido à limitação do matplotlib"
                    )

                # Checagem de segurança
                if not colunas_a_plotar:
                    return (
                        "[ERRO] Nenhuma coluna numérica válida encontrada para plotar."
                    )

                # Calcular grid de subplots
                n_cols = min(6, len(colunas_a_plotar))
                n_rows = (len(colunas_a_plotar) + n_cols - 1) // n_cols

                plt.figure(figsize=(20, 4 * n_rows))

                # Itera sobre a lista de colunas A PLOTAR (colunas_a_plotar)
                for i, col in enumerate(colunas_a_plotar):
                    plt.subplot(n_rows, n_cols, i + 1)
                    plt.hist(
                        self.df[col].dropna(),
                        bins=30,
                        alpha=0.7,
                        color="skyblue",
                        edgecolor="black",
                    )
                    plt.title(f"{col}", fontsize=10)
                    plt.xlabel(col, fontsize=8)
                    plt.ylabel("Freq.", fontsize=8)
                    plt.xticks(fontsize=7)
                    plt.yticks(fontsize=7)

                plt.suptitle(titulo, fontsize=16, y=0.98)
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])

            elif tipo_grafico == "dispersao":
                if len(colunas) < 2:
                    return "[ERRO] Gráfico de dispersão requer no mínimo duas colunas."

                plt.figure(figsize=(10, 6))
                x_col, y_col = colunas[0], colunas[1]

                if x_col not in self.df.columns or y_col not in self.df.columns:
                    return (
                        f"[ERRO] Uma das colunas não foi encontrada: {x_col}, {y_col}"
                    )

                plt.scatter(self.df[x_col], self.df[y_col], alpha=0.6, color="coral")
                plt.title(titulo)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, alpha=0.3)

            elif tipo_grafico == "boxplot":

                # Definir colunas-alvo
                if not colunas:
                    # Comportamento padrão: Se nenhuma for especificada, usa as primeiras 5 numéricas
                    colunas_alvo = self.df.select_dtypes(
                        include=[np.number]
                    ).columns.tolist()[:5]
                else:
                    colunas_alvo = colunas

                # --- CORREÇÃO: Filtrar apenas colunas numéricas ---
                colunas_validas = []
                for col in colunas_alvo:
                    if col in self.df.columns:
                        # Verifica se a coluna é numérica (ignorando colunas de texto/objeto)
                        if pd.api.types.is_numeric_dtype(self.df[col]):
                            colunas_validas.append(col)
                        else:
                            print(f"⚠️ Boxplot ignorado: Coluna '{col}' não é numérica.")

                if not colunas_validas:
                    # Retorno de erro otimizado para o Agente identificar
                    return "[ERRO AGENTE] Nenhuma coluna numérica válida foi encontrada na seleção para plotar o boxplot. Tente novamente especificando colunas numéricas."

                plt.figure(figsize=(12, 6))
                dados_boxplot = []
                labels_boxplot = []

                for col in colunas_validas:  # Itera sobre a lista FILTRADA
                    dados_boxplot.append(self.df[col].dropna())
                    labels_boxplot.append(col)

                plt.boxplot(dados_boxplot, labels=labels_boxplot)
                plt.title(titulo)
                plt.ylabel("Valores")
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)

            elif tipo_grafico == "barras":
                if len(colunas) < 2:
                    return "[ERRO] Gráfico de barras requer duas colunas: categoria e valor."

                plt.figure(figsize=(12, 6))
                cat_col, val_col = colunas[0], colunas[1]

                if cat_col not in self.df.columns or val_col not in self.df.columns:
                    return f"[ERRO] Uma das colunas não foi encontrada: {cat_col}, {val_col}"

                dados_agrupados = (
                    self.df.groupby(cat_col)[val_col].sum().head(20)
                )  # Top 20
                dados_agrupados.plot(kind="bar", color="lightgreen")
                plt.title(titulo)
                plt.xlabel(cat_col)
                plt.ylabel(val_col)
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)

            else:
                return f"[ERRO] Tipo de gráfico não suportado: {tipo_grafico}. Use: histograma, dispersao, boxplot, barras, multiplos_histogramas"

            # Salvar o gráfico
            outputs_dir = Path("outputs")
            outputs_dir.mkdir(exist_ok=True)
            timestamp = str(int(pd.Timestamp.now().timestamp()))
            caminho_imagem = outputs_dir / f"grafico_{timestamp}.png"

            plt.tight_layout()
            plt.savefig(caminho_imagem, dpi=300, bbox_inches="tight", facecolor="white")
            plt.close()  # Importante: fechar a figura para liberar memória

            print(f"📊 Gráfico salvo em: {caminho_imagem}")
            return str(caminho_imagem)

        except Exception as e:
            plt.close()  # Garantir que fechamos a figura mesmo em caso de erro
            return f"[ERRO] Falha ao gerar o gráfico: {e}"
