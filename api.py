import json
import os
import shutil
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent_utils import Utils
from fluxo import FluxoEDA

app = FastAPI(
    title="Agente de Análise de Dados para CSV",
    description="Uma API que orquestra um time de agentes para realizar Análise Exploratória de Dados em qualquer arquivo CSV.",
    version="1.0.0",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar o diretório de uploads se ele não existir
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Criar o diretório de outputs se ele não existir
OUTPUTS_DIR = Path("./outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)


# Função de limpeza para BackgroundTasks
def remove_file(path: str) -> None:
    """Deleta um arquivo após o processamento."""
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"🗑️ Arquivo removido: {path}")
    except Exception as e:
        print(f"⚠️ Erro ao remover arquivo {path}: {e}")


def remove_directory(path: str) -> None:
    """Remove um diretório após o processamento."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"🗑️ Diretório removido: {path}")
    except Exception as e:
        print(f"⚠️ Erro ao remover diretório {path}: {e}")


@app.post("/chat/")
async def chat_with_agent(
    file: Annotated[UploadFile, File()],
    question: Annotated[str, Form()],
    background_tasks: BackgroundTasks,
):
    """
    Endpoint principal para interagir com o agente de dados.
    Recebe um arquivo CSV e uma pergunta, e retorna a análise do agente.
    """
    try:
        print(f"📥 Recebido arquivo: {file.filename}")
        print(f"❓ Pergunta: {question}")

        # Salvar o arquivo temporariamente no diretório de uploads
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Determinar o caminho para o CSV, descompactando se for um ZIP
        if file_path.suffix == ".zip":
            pasta_extraida = OUTPUTS_DIR / file_path.stem
            Utils.verificar_e_descompactar(str(pasta_extraida), str(file_path))
            arquivos_csv = list(pasta_extraida.glob("*.csv"))
            if not arquivos_csv:
                return {"error": "Nenhum arquivo CSV encontrado dentro do arquivo ZIP."}
            caminho_csv = str(arquivos_csv[0])
            background_tasks.add_task(remove_directory, str(pasta_extraida))
        elif file_path.suffix == ".csv":
            caminho_csv = str(file_path)
        else:
            return {
                "error": "Formato de arquivo não suportado. Por favor, use .csv ou .zip."
            }

        # Adicionar tarefa de exclusão do arquivo de upload original
        background_tasks.add_task(remove_file, str(file_path))

        # Inicializar e executar o fluxo de EDA
        print("🚀 Iniciando FluxoEDA...")
        fluxo = FluxoEDA(caminho_csv=caminho_csv)

        response_data = fluxo.executar(question)
        print(f"✅ Resposta do fluxo recebida")
        print(f"🔍 Tipo da resposta: {type(response_data)}")

        # --- NOVO BLOCO DE PROCESSAMENTO SIMPLIFICADO ---

        if isinstance(response_data, dict) and response_data.get("image_url"):
            # Caso 1: Retorno é um Gráfico (Contém 'image_url')
            # O fluxo.py já retornou o URL local completo (ex: outputs/grafico_XYZ.png).
            # Precisamos extrair o nome do arquivo para construir o URL acessível pelo front-end (http://localhost:8000/outputs/...).

            # O fluxo.py agora retorna um dicionário com "image_url"
            image_url_local = response_data["image_url"]

            # O nome do arquivo está no final da string do caminho.
            chart_filename = Path(image_url_local).name

            print(f"📊 Gráfico detectado: {chart_filename}")
            return {
                "response": response_data.get(
                    "text", "Gráfico gerado com sucesso."
                ),  # Retorna texto ou um padrão
                "image_url": f"/outputs/{chart_filename}",
            }

        elif isinstance(response_data, dict) and response_data.get("response"):
            # Caso 2: Retorno é Análise/Conclusão (Contém 'response')
            # Retorna o dicionário de texto
            return response_data

        else:
            # Fallback para erros ou retornos inesperados do CrewAI
            return {
                "error": f"Formato de resposta inesperado do agente: {response_data}"
            }

    except Exception as e:
        print(f"❌ Erro na API: {e}")
        import traceback

        traceback.print_exc()
        return {"error": f"Erro interno: {str(e)}"}


# Endpoint para servir arquivos de saída (gráficos)
@app.get("/outputs/{filename}")
async def serve_output_file(filename: str):
    """Serve arquivos da pasta outputs (gráficos gerados)"""
    file_path = OUTPUTS_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    else:
        return {"error": "Arquivo não encontrado"}


# Endpoint de teste para verificar se a API está funcionando
@app.get("/test")
async def test_endpoint():
    """Endpoint de teste"""
    return {
        "status": "OK",
        "message": "API está funcionando!",
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


# Endpoint para servir o index.html na raiz
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open(os.path.join("frontend", "index.html"), encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend não encontrado</h1><p>Certifique-se de que a pasta 'frontend' existe.</p>",
            status_code=404,
        )


# Servir arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
