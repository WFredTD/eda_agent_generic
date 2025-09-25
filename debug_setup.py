#!/usr/bin/env python3
"""
Script de diagnóstico para verificar a configuração do projeto CrewAI
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Verifica a versão do Python"""
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERRO: Python 3.8+ é necessário")
        return False
    print("✅ Versão do Python OK")
    return True


def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required_packages = [
        "crewai",
        "pandas",
        "matplotlib",
        "seaborn",
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "openai",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NÃO INSTALADO")
            missing.append(package)

    if missing:
        print(f"\n📦 Para instalar os pacotes faltando:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True


def check_crewai_version():
    """Verifica a versão do CrewAI"""
    try:
        import crewai

        version = getattr(crewai, "__version__", "desconhecida")
        print(f"CrewAI versão: {version}")

        # Testa importações específicas
        from crewai import LLM, Agent, Crew, Process, Task

        print("✅ Importações do CrewAI OK")
        return True
    except Exception as e:
        print(f"❌ Erro com CrewAI: {e}")
        return False


def check_env_file():
    """Verifica o arquivo .env"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado")
        print("Crie um arquivo .env com:")
        print("OPENAI_API_KEY=sua-chave-aqui")
        return False

    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY não configurada no .env")
        return False

    if api_key.startswith("sk-") and len(api_key) > 20:
        print("✅ OPENAI_API_KEY configurada")
        return True
    else:
        print("⚠️ OPENAI_API_KEY parece inválida")
        return False


def check_directories():
    """Verifica se os diretórios necessários existem"""
    dirs = ["uploads", "outputs", "frontend"]
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ Diretório {dir_name}/")
        else:
            print(f"⚠️ Diretório {dir_name}/ não existe (será criado automaticamente)")


def test_openai_connection():
    """Testa conexão com OpenAI"""
    try:
        import os

        from crewai import LLM

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Não é possível testar - API key não configurada")
            return False

        llm = LLM(model="gpt-4o-mini", api_key=api_key)
        print("✅ Configuração LLM criada com sucesso")
        return True

    except Exception as e:
        print(f"❌ Erro ao configurar LLM: {e}")
        return False


def test_basic_crewai():
    """Teste básico do CrewAI"""
    try:
        import os

        from crewai import LLM, Agent, Crew, Task

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Não é possível testar - API key não configurada")
            return False

        llm = LLM(model="gpt-4o-mini", api_key=api_key)

        # Criar um agente simples
        agent = Agent(
            role="Test Agent", goal="Test goal", backstory="Test backstory", llm=llm
        )

        print("✅ Agente criado com sucesso")
        return True

    except Exception as e:
        print(f"❌ Erro ao criar agente: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Função principal de diagnóstico"""
    print("🔍 DIAGNÓSTICO DO SISTEMA CrewAI")
    print("=" * 50)

    checks = [
        ("Versão Python", check_python_version),
        ("Dependências", check_dependencies),
        ("CrewAI", check_crewai_version),
        ("Arquivo .env", check_env_file),
        ("Diretórios", check_directories),
        ("Configuração LLM", test_openai_connection),
        ("Teste básico CrewAI", test_basic_crewai),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 Verificando {name}...")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("📊 RESUMO:")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print(f"\n{passed}/{total} verificações passaram")

    if passed == total:
        print("\n🎉 Sistema configurado corretamente!")
    else:
        print(
            f"\n⚠️ {total - passed} problemas encontrados. Corrija-os antes de continuar."
        )


if __name__ == "__main__":
    main()
