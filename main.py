import argparse
import logging
import os
import sys

from config import LOG_LEVEL, ZEN_MODEL, ZEN_TIMEOUT
from orquestrador import executar_pipeline

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def exemplo_interativo(diretorio_personalizado: str | None = None):
    if diretorio_personalizado:
        os.chdir(diretorio_personalizado)
        logger.info("Diretorio de trabalho alterado para: %s", diretorio_personalizado)

    print("=" * 60)
    print("  RAFAEL CODE - Multi-Agente (7 Agentes)")
    print("  Pipeline com duplo loop de correcao")
    print(f"  Modelo: {ZEN_MODEL} via OpenCode Zen")
    print(f"  URL: {os.getenv('ZEN_API_URL', 'https://opencode.ai/zen/v1/responses')}")
    print(f"  Diretorio: {os.getcwd()}")
    print(f"  Timeout: {ZEN_TIMEOUT}s")
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
    print(resultado)

    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Orquestrador Multi-Agente com Big Pickle via OpenCode Zen"
    )
    parser.add_argument(
        "--diretorio",
        type=str,
        default=None,
        help="Caminho do diretorio do projeto a ser analisado. "
             "Se nao informado, usa o padrao da Constituicao.",
    )
    args = parser.parse_args()

    resultado = exemplo_interativo(diretorio_personalizado=args.diretorio)
    sys.exit(0 if "Falha" not in resultado else 1)
