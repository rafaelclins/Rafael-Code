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
        logger.info("Diretorio de trabalho alterado para: %s", diretorio)

    print("=" * 60)
    print("  RAFAEL CODE - Multi-Agente (7 Agentes)")
    print("  Pipeline com duplo loop de correcao")
    print(f"  Modelo: {ZEN_MODEL} via OpenCode Zen")
    print(f"  URL: https://opencode.ai/zen/v1/responses")
    print(f"  Diretorio: {os.getcwd()}")
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
    args = parser.parse_args()

    if args.version:
        print(f"Rafael Code v{APP_VERSION}")
        sys.exit(0)

    if args.verbose:
        import ollama_client
        ollama_client.VERBOSE_MODE = True

    resultado = exemplo_interativo(diretorio=args.diretorio)
    sys.exit(0 if resultado.success else 1)
