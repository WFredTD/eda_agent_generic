🔎 Agente de Análise Exploratória de Dados (EDA) Genérico
==========================================================================

Visão Geral do Projeto
----------------------

O `eda_agent_generic` é um sistema de Agentes Autônomos (CrewAI) projetado para automatizar a Análise Exploratória de Dados (EDA) de forma **genérica**. Ele aceita qualquer arquivo **CSV ou ZIP** contendo dados e é capaz de responder a perguntas complexas, realizar cálculos estatísticos e gerar visualizações gráficas de alta qualidade, garantindo que as conclusões sejam puramente **fatuais**.

Este projeto resolve os desafios comuns de instabilidade de LLMs e gasto excessivo de tokens ao implementar uma arquitetura de fluxo de trabalho rigorosa e mecanismos de recuperação de falhas.

🚀 Tecnologias Utilizadas
-------------------------

<p align='center'>
    <img loading="lazy" src="https://skillicons.dev/icons?i=python,fastapi,git,github,js,html,css,md,vscode"/> 
</p>
<p align='center'>
    <img src="https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white" alt="Badge Pandas">
    <img src="https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black" alt="Badge Matplotlib">
    <img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white" alt="Badge NumPy">
</p>

### Além disso tbm foi usado:

-   **CrewAI** para **Orquestração de Agentes** 

-   **OpenAI (GPT-4o-mini)** como **Modelo de Linguagem**

-   **Matplotlib** e **Seaborn** par **Data Science & Visualização**

🧠 Arquitetura e Funcionalidades
--------------------------------

O projeto opera com uma arquitetura de **Segregação Estrita** e um time de três agentes com responsabilidades únicas.

### 1\. O Time de Agentes

| Agente | Principal Responsabilidade |
| --- | --- |
| **Especialista em Análise de Dados** | Executa códigos Python (`pandas`) para extrair estatísticas (média, mediana, outliers) e fatos numéricos. |
| **Especialista em Geração de Gráficos** | Traduz requisições em parâmetros e gera arquivos PNG, seguindo o **Caminho Gráfico**. |
| **Consultor Estratégico de Dados** | Sintetiza resultados factuais (incluindo gráficos na memória) em conclusões acionáveis, seguindo o **Caminho Análise**. |


### 2\. Mecanismos de Robustez e Estabilidade

A estabilidade do `eda_agent_generic` é garantida pelos seguintes mecanismos:

-   **Segregação de Fluxo (Anti-Confusão):** O sistema detecta a intenção da pergunta (gráfica ou analítica) e segue um caminho único. Uma requisição de análise **NUNCA** retorna um gráfico, e uma requisição de gráfico **NUNCA** retorna uma análise textual, eliminando a confusão de contexto e a descrição incorreta de gráficos.

-   **Validação de Parâmetros de Gráfico:** O esquema **Pydantic** é usado na `PlotarGraficoTool` para validar rigorosamente o `tipo_grafico`, as `colunas` e o `titulo`, prevenindo loops de validação.

-   **Tratamento de Colunas:** As ferramentas de visualização filtram colunas não numéricas e priorizam subconjuntos de colunas (para evitar a plotagem de 80 gráficos), impedindo *runtime errors* e garantindo a eficiência.

-   **Atribuição Forçada de Saída:** A ferramenta `QueryCSVGenerico` força a atribuição da última expressão Python à variável `resultado`, evitando loops de raciocínio do agente de análise por não conseguir extrair dados.

-   **Recuperação de Falha Elegante:** O Agente de Geração de Gráficos é instruído por um **prompt de emergência** a retornar uma mensagem de erro clara e útil em vez de entrar em *timeout* ou loops, otimizando o gasto de tokens.

* * * * *

🛠 Como Rodar o Projeto Localmente
----------------------------------

Siga estas instruções para configurar e rodar o projeto em sua máquina.

### Pré-requisitos

-   Python 3.8+

-   Sua chave de API da OpenAI.

### 1\. Configuração do Ambiente


```
# 1. Clone o repositório
git clone https://https://github.com/WFredTD/eda_agent_generic
cd eda_agent_generic

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows, use: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

```

### 2\. Configuração da Chave de API

Crie um arquivo chamado **`.env`** na raiz do projeto e insira sua chave da OpenAI no seguinte formato:

```
OPENAI_API_KEY=sua-chave-aqui

```

### 3\. Execução do Servidor

Inicie a aplicação FastAPI usando Uvicorn. O servidor será iniciado em `http://127.0.0.1:8000`.


```
uvicorn api:app --reload

```

### 4\. Acesso ao Chat

Abra seu navegador e acesse:

```
http://127.0.0.1:8000

```

Você pode arrastar e soltar um arquivo CSV (como o `Kaggle - Credit Card Fraud.zip` ou o `AmesHousing.csv`) para começar a interagir com o agente.

* * * * *

📄 Licença
----------

Este projeto está sob a licença **MIT**. Você tem a liberdade de usar, modificar e distribuir o código, desde que o aviso de direitos autorais e a licença original sejam mantidos.

* * * * *

📧 Contato
----------
<div>
    <a href = "mailto:fredtorresdreyer@gmail.com"><img loading="lazy" src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white" target="_blank"></a>
    <a href="https://www.linkedin.com/in/walterftdreyer/" target="_blank"><img loading="lazy" src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" target="_blank"></a> 
</div>