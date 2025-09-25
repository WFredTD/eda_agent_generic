import os
import threading
import time
from pathlib import Path

import pandas as pd
from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

from custom_tool_generico import PlotarGraficoTool, QueryCSVGenerico

load_dotenv()


class FluxoEDA:
    """
    Orquestrador principal para a Análise Exploratória de Dados.
    """

    def __init__(self, caminho_csv: str):
        self.caminho_csv = caminho_csv
        # Carregar o DataFrame na inicialização para que todos os agentes o utilizem
        try:
            self.df = pd.read_csv(caminho_csv)
            print(f"✅ DataFrame carregado com sucesso do arquivo: {self.caminho_csv}")
            print(f"📊 Shape: {self.df.shape}")
            print(f"📋 Colunas disponíveis: {list(self.df.columns)}")
        except Exception as e:
            raise Exception(f"❌ Erro ao carregar o CSV: {e}")

    def executar(self, pergunta: str) -> dict | str:
        """
        Executa o fluxo de trabalho do agente, com segregação estrita.

        Args:
            pergunta (str): A pergunta do usuário.

        Returns:
            dict | str: Dicionário com caminho do gráfico (se for gráfico) ou string com a resposta textual.
        """
        # Verificar configuração da API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY não encontrada. Configure no arquivo .env")

        # Configurar LLM explicitamente
        llm_config = LLM(model="gpt-4o-mini", api_key=api_key, temperature=0.1)

        # Injetar o DataFrame nas ferramentas
        query_tool = QueryCSVGenerico()
        query_tool.df = self.df
        plot_tool = PlotarGraficoTool()
        plot_tool.df = self.df

        # --- DEFINIÇÃO DOS AGENTES COM PROMPTS REFORÇADOS ---

        # Agente 1: Analista de Dados (Análise Pura)
        analista_de_dados = Agent(
            role="Especialista em Análise de Dados e Programação Python",
            goal="Traduzir a pergunta do usuário em código Python para analisar um DataFrame chamado 'df' e extrair insights relevantes.",
            backstory=(
                "Você é um cientista de dados sênior, com foco exclusivo em Análise Exploratória de Dados (EDA). "
                "Sua missão é usar seu conhecimento em 'pandas' para responder a perguntas, **sempre se baseando apenas nos dados do DataFrame 'df'**. "
                "Seu processo de pensamento é estritamente lógico e factual. Você não tem conhecimento do mundo real ou de outros datasets além do que é fornecido. "
                "Você usa a ferramenta 'Ferramenta de execucao de codigo de consulta a um CSV' para executar código Python. "
                "Seu código deve ser otimizado para extrair a informação solicitada e o resultado final deve ser atribuído à variável 'resultado'. "
                "**IMPORTANTE**: Se a pergunta não puder ser respondida com os dados disponíveis no DataFrame, sua resposta deve ser: 'Não é possível responder a essa pergunta com os dados disponíveis.' "
                "Você **NUNCA** cria gráficos; seu único trabalho é a análise numérica e estatística. "
                "Siga o seguinte formato para pensar e agir:\n"
                "Thought: Avalie a pergunta. Determine qual código Python é necessário para obter a resposta. "
                "Action: Use a ferramenta 'Ferramenta de execucao de codigo de consulta a um CSV' com o código Python planejado. "
                "Action Input: O código Python para execução. "
                "Observation: O resultado da execução do código. "
                "Thought: Analise a 'Observation' e use-a para formar uma resposta clara. Se a 'Observation' indicar um erro, reavalie a abordagem. "
            ),
            tools=[query_tool],
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        # Agente 2: Gerador de Gráficos (Apenas Geração de Imagem)
        gerador_de_graficos = Agent(
            role="Especialista em Geração de Gráficos de Dados",
            goal="Gerar o gráfico solicitado pelo usuário usando a ferramenta e retornar APENAS o caminho do arquivo de imagem.",
            backstory=(
                "Você é um técnico de visualização altamente focado. Sua única tarefa é traduzir solicitações de gráficos em uma entrada de ferramenta perfeita. "
                "Você **NUNCA** deve analisar os dados ou escrever qualquer texto de resumo/conclusão. "
                "Seu output final deve ser estritamente o caminho do arquivo de imagem PNG gerado pela ferramenta. "
                "Você usa a ferramenta 'Ferramenta de geracao de grafico', que espera os argumentos tipo_grafico, colunas e titulo. "
                "**REGRA DE FALHA:** Se a ferramenta retornar um erro interno (por exemplo, colunas não numéricas ou tipo de gráfico incorreto), você DEVE retornar a seguinte mensagem EXATA como sua Final Answer: 'Erro na Geração: Ocorreu um erro interno. Verifique se as colunas são numéricas e tente novamente.' "
                "**REGRA DE FALHA E OTIMIZAÇÃO:** Se a 'Observation' da sua ferramenta retornar a palavra '[ERRO]', '[AVISO]' ou a mensagem 'Nenhuma coluna numérica válida', você DEVE imediatamente PARAR AS TENTATIVAS e retornar a seguinte mensagem EXATA como sua Final Answer: 'Erro na Geração: A solicitação não pôde ser atendida. Verifique se as colunas são numéricas e se o tipo de gráfico é apropriado.'"
            ),
            tools=[plot_tool],
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        # Agente 3: Consultor Estratégico (Análise e Conclusão Pura)
        conclusor_estrategico = Agent(
            role="Consultor Estratégico de Dados e Validador de Análise",
            goal="Sintetizar resultados de análises e visualizações em conclusões estratégicas e de alto nível, garantindo a coerência e a relevância das informações.",
            backstory=(
                "Você é um consultor de alto nível e a última linha de defesa contra alucinações. "
                "Sua missão é: 1. Revisar as informações para garantir que são coerentes e relevantes para a pergunta original. 2. Identificar e ignorar quaisquer informações que pareçam incorretas ou alucinadas. 3. Usar a memória (incluindo gráficos gerados anteriormente) para basear suas conclusões, mas **NUNCA** gerar ou descrever um gráfico na resposta final. "
                "Você deve se basear APENAS nos fatos validados e nas suas análises internas para criar uma narrativa coesa e objetiva. "
                "Você **NÃO** deve adicionar contexto de negócio (como 'vendas', 'marketing', 'clientes') que não esteja explicitamente no output da análise."
            ),
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        # --- LÓGICA CONDICIONAL DE DOIS CAMINHOS (GRÁFICO VS ANÁLISE) ---

        # Palavras que indicam uma solicitação IMPERATIVA de gráfico (Caminho 1)
        palavras_grafico_imperativo = ["gere", "crie", "faça", "mostre", "plote"]
        palavras_grafico = [
            "gráfico",
            "grafico",
            "plot",
            "visualização",
            "visualizacao",
            "chart",
            "distribuição",
            "distribuicao",
            "histograma",
            "boxplot",
            "dispersão",
            "barras",
            "scatter",
        ]

        is_imperative_graph_request = any(
            word in pergunta.lower() for word in palavras_grafico_imperativo
        ) and any(word in pergunta.lower() for word in palavras_grafico)

        if is_imperative_graph_request:
            # CAMINHO 1: Solicitação de Geração de Gráfico (Apenas Geração)

            # Ajustando a tarefa de gráfico para o novo formato de argumento (separado, não dict dentro de input_data)
            tarefa_grafico = Task(
                description=(
                    f"Gere o gráfico solicitado pelo usuário: '{pergunta}'.\n\n"
                    f"Colunas do DataFrame disponíveis: {list(self.df.columns)}\n\n"
                    "INSTRUÇÃO DE SAÍDA: O Agente de Visualização **DEVE** retornar APENAS o caminho do arquivo PNG gerado. Não gere texto descritivo ou de análise."
                ),
                expected_output="O caminho completo do arquivo PNG do gráfico gerado na pasta outputs/, sem qualquer texto adicional.",
                agent=gerador_de_graficos,
            )

            tarefas = [tarefa_grafico]

        else:
            # CAMINHO 2: Análise/Conclusão (Análise Pura, com uso da memória)

            # Tarefa 1: Análise Factual
            tarefa_analise = Task(
                description=(
                    f"Com base na pergunta do usuário: '{pergunta}', execute uma análise de dados.\n\n"
                    f"Informações do dataset:\n"
                    f"- Shape: {self.df.shape}\n"
                    f"- Colunas disponíveis: {list(self.df.columns)}\n\n"
                    "Sua tarefa é usar a ferramenta `Ferramenta de execucao de codigo de consulta a um CSV` para escrever e executar um código Python que responda diretamente à pergunta. "
                    "O resultado da sua análise, em formato de texto, deve ser conciso e objetivo. "
                    "Você deve se ater estritamente aos dados extraídos e não fazer suposições ou usar conhecimento externo."
                ),
                expected_output="Uma análise textual clara, baseada em dados, com estatísticas e fatos obtidos do DataFrame.",
                agent=analista_de_dados,
            )

            # Tarefa 2: Conclusão Estratégica (Usando Análise Factual + Memória)
            tarefa_conclusao = Task(
                description=(
                    "Sintetize todos os resultados das tarefas anteriores em uma resposta final clara, baseada **estritamente na análise de dados**. "
                    "Você deve focar em apresentar os fatos e as conclusões obtidas diretamente do DataFrame. "
                    "Não adicione contexto de negócio (como 'vendas', 'marketing', 'clientes') que não está presente nos dados. "
                    "\n\nInclua:\n"
                    "1. Um resumo dos principais achados da análise (por exemplo, estatísticas, distribuições, outliers).\n"
                    "2. Se gráficos anteriores (na memória) forem relevantes, use-os como base para a sua análise, mas **NUNCA** mencione o caminho do arquivo ou inclua imagens na sua resposta.\n"
                    "3. Conclusões objetivas sobre os dados, como padrões identificados ou a ausência de correlações significativas.\n"
                    "4. Recomendações baseadas nos achados, focando em como aprofundar a análise de dados (ex: 'recomenda-se investigar os outliers', 'explorar a correlação entre V1 e V2').\n\n"
                    "Formato: Resposta clara, objetiva e puramente analítica para o usuário."
                ),
                expected_output="Resposta final estruturada com insights e conclusões focadas em dados, sem inferências de negócio.",
                agent=conclusor_estrategico,
            )

            tarefas = [tarefa_analise, tarefa_conclusao]

        # Criar a Crew com processo SEQUENCIAL
        crew = Crew(
            agents=[analista_de_dados, gerador_de_graficos, conclusor_estrategico],
            tasks=tarefas,
            process=Process.sequential,
            verbose=True,
        )

        try:
            # Executar o fluxo com timeout
            result_container = [None]
            exception_container = [None]

            def run_crew():
                try:
                    result_container[0] = crew.kickoff()
                except Exception as e:
                    exception_container[0] = e

            crew_thread = threading.Thread(target=run_crew)
            crew_thread.daemon = True
            crew_thread.start()

            crew_thread.join(timeout=300)

            if crew_thread.is_alive():
                print("⏰ Timeout: Execução excedeu 5 minutos")
                return "A análise está levando mais tempo que o esperado. Tente uma pergunta mais simples."

            if exception_container[0]:
                raise exception_container[0]

            result = result_container[0]

            # Obter o texto final do resultado da crew
            result_text = str(result.output if hasattr(result, "output") else result)

            # --- SEGREGAÇÃO DE RETORNO FINAL ---

            if is_imperative_graph_request:
                # Se for um pedido de gráfico, o resultado do kickoff é o caminho do arquivo (do gerador_de_graficos)
                # O método `api.py` irá usar esse caminho para exibir o gráfico.

                # Buscar o arquivo gerado (é a maneira mais segura)
                outputs_dir = Path("outputs")
                chart_files = (
                    list(outputs_dir.glob("*.png")) if outputs_dir.exists() else []
                )

                if chart_files:
                    # Pegar o gráfico mais recente (que é o que o agente acabou de gerar)
                    latest_chart = max(chart_files, key=lambda p: p.stat().st_mtime)
                    chart_name = latest_chart.name
                    print(f"📊 Gráfico detectado: {chart_name}")

                    # Retorna o formato esperado pela API para exibir a imagem no chat
                    return {
                        "text": "",  # Sem texto, apenas a imagem
                        "image_url": f"http://localhost:8000/outputs/{chart_name}",
                    }

                # Fallback em caso de erro na geração
                return "O agente tentou gerar o gráfico, mas não encontrou o arquivo na pasta de saída. Verifique o log do terminal."

            else:
                # Retorna apenas o texto de conclusão
                print(f"✅ Resultado final processado: {result_text[:200]}...")
                return {"response": result_text}

        except Exception as e:
            print(f"❌ Erro na execução do crew: {e}")
            import traceback

            traceback.print_exc()

            # Tentar limpeza de recursos
            try:
                import matplotlib.pyplot as plt

                plt.close("all")
            except:
                pass

            return {
                "error": f"Erro durante a análise: {str(e)}. Tente reformular sua pergunta."
            }
        finally:
            # Garantir limpeza
            try:
                import matplotlib.pyplot as plt

                plt.close("all")
            except:
                pass
