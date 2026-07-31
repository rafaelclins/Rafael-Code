import argparse
import logging
import os
import sys

from config import APP_VERSION, LOG_LEVEL, ZEN_MODEL
from orquestrador import PipelineResult, executar_pipeline

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("main")


def exemplo_interativo(diretorio: str | None = None) -> PipelineResult:
    if diretorio:
        os.chdir(diretorio)
        logger.info("Diretório de trabalho alterado para: %s", diretorio)

    print("=" * 60)
    print("  RAFAEL CODE - Multi-Agente (7 Agentes)")
    print("  Pipeline com duplo loop de correção")
    print(f"  Modelo: {ZEN_MODEL} via OpenCode Zen")
    print(f"  URL: https://opencode.ai/zen/v1/responses")
    print(f"  Diretório: {os.getcwd()}")
    print(f"  Timeout: connect=30s, read=600s")
    print("=" * 60)

    pedido = input("\nDigite seu pedido (ou ENTER para usar exemplo): ").strip()
    if not pedido:
        pedido = (
            "Preciso criar um portifolio React + Tailwind CSS hospedado "
            "com custo zero real, sem cartao de credito, com HTTPS e "
            "deploy automatico via Git."
        )
        print(f"\nUsando exemplo: {pedido}")

    print("\n--- Iniciando pipeline ---\n")
    resultado = executar_pipeline(pedido)

    print("\n" + "=" * 60)
    print("  RESULTADO FINAL")
    print("=" * 60)
    print(resultado.text)

    return resultado


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    parser = argparse.ArgumentParser(
        description="Orquestrador Multi-Agente com Big Pickle via OpenCode Zen"
    )
    parser.add_argument(
        "--diretorio",
        type=str,
        default=None,
        help="Caminho do diretorio do projeto a ser analisado.",
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Exibe a versao e sai.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Exibe o JSON bruto trocado entre os agentes.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Modo headless para CI/CD: sem input(), sem spinner, falha rapida.",
    )
    args = parser.parse_args()

    if args.version:
        print(f"Rafael Code v{APP_VERSION}")
        sys.exit(0)

    if args.verbose:
        import ollama_client
        ollama_client.VERBOSE_MODE = True

    if args.headless:
        import ollama_client
        ollama_client.HEADLESS_MODE = True
        pedido = (
            "Analise todos os arquivos de codigo deste diretorio atual "
            "e valide se existem bugs de sintaxe, erros de logica ou "
            "brechas de seguranca."
        )
        resultado = executar_pipeline(pedido, headless=True)
        sys.exit(0 if resultado.success else 1)
    else:
        resultado = exemplo_interativo(diretorio=args.diretorio)
        sys.exit(0 if resultado.success else 1)
