import logging
import os

from agentes import (
    AGENTE_1_ALINHADOR,
    AGENTE_2_PLANEJADOR,
    AGENTE_3_PESQUISADOR,
    AGENTE_4_EXECUTOR,
    AGENTE_5_CONSOLIDADOR,
    AGENTE_5_REFAZ_POR_SEGURANCA,
    AGENTE_6_AVALIADOR,
    AGENTE_7_GUARDIAO,
)
from config import MAX_REPROVACAO_QUALIDADE, MAX_REPROVACAO_SEGURANCA
from ollama_client import ErroModelo, aquecer_modelo, chamar_agente, criar_sessao
from schemas import (
    AlinhadorOutput,
    AvaliadorOutput,
    ConsolidadorOutput,
    ExecutorOutput,
    GuardiaoOutput,
    PesquisadorOutput,
    PlanejadorOutput,
)

logger = logging.getLogger(__name__)


def _ler_contexto_repositorio(max_caracteres: int = 1000) -> str:
    linhas: list[str] = []
    for f in sorted(os.listdir(".")):
        if not f.endswith(".py"):
            continue
        try:
            with open(f, "r", encoding="utf-8") as arq:
                conteudo = "".join(arq.readlines()[:50])
                linhas.append(f"--- {f} ---\n{conteudo}")
        except Exception:
            pass
    contexto = "\n\n".join(linhas)
    return contexto[:max_caracteres]


def _limitar(texto: str, max_caracteres: int) -> str:
    if len(texto) <= max_caracteres:
        return texto
    return texto[:max_caracteres] + "\n\n...[TRUNCADO]"


def _safe_print(texto: str) -> None:
    try:
        print(texto)
    except UnicodeEncodeError:
        print(repr(texto)[1:-1])


def _print_separador(titulo: str) -> None:
    _safe_print("")
    _safe_print("=" * 55)
    _safe_print("  " + titulo)
    _safe_print("=" * 55)


def _print_agente(numero: int, nome: str, status: str = "") -> None:
    siglas = ["", "[A1]", "[P2]", "[R3]", "[E4]", "[C5]", "[A6]", "[G7]"]
    sigla = siglas[numero] if numero < len(siglas) else f"[A{numero}]"
    suf = f" [{status}]" if status else ""
    _safe_print("")
    _safe_print(f"{sigla} --- AGENTE {numero}: {nome}{suf} ---")
    _safe_print("-" * 55)


def executar_pipeline(pedido_usuario: str, aquecer: bool = True) -> str:
    try:
        return _executar_pipeline_interno(pedido_usuario, aquecer)
    except ErroModelo as e:
        msg = f"Erro no modelo local: {e.mensagem}"
        logger.error(msg)
        _safe_print("")
        _safe_print(f"  ERRO: {msg}")
        return msg


def _executar_pipeline_interno(pedido_usuario: str, aquecer: bool = True) -> str:
    _print_separador("ORQUESTRADOR MULTI-AGENTE INICIADO")
    _safe_print(f"  Pedido: {pedido_usuario[:80]}{'...' if len(pedido_usuario) > 80 else ''}")
    logger.info("Iniciando pipeline multi-agente para o pedido do usuario.")

    sessao = criar_sessao()
    if aquecer:
        _safe_print("  Aquecendo modelo...")
        aquecer_modelo(sessao)

    _print_agente(1, "ALINHADOR (Orchestrator)")
    dados_agente_1 = chamar_agente(
        AGENTE_1_ALINHADOR, pedido_usuario, AlinhadorOutput
    )
    logger.info("Agente 1 (Alinhador) concluido.")
    _safe_print(f"  Objetivo: {dados_agente_1.get('objetivo_principal', 'N/A')[:100]}")

    tentativas_qualidade = 0
    feedback_qualidade = ""

    while tentativas_qualidade < MAX_REPROVACAO_QUALIDADE:
        _print_separador(
            f"CICLO DE QUALIDADE {tentativas_qualidade + 1}/{MAX_REPROVACAO_QUALIDADE}"
        )

        entrada_planejador = _limitar(str(dados_agente_1), 2000)
        if feedback_qualidade:
            entrada_planejador += (
                f"\n[CORRECAO OBRIGATORIA]: O avaliador reprovou o ciclo anterior "
                f"pelo motivo: {feedback_qualidade}"
            )
            entrada_planejador = _limitar(entrada_planejador, 2500)
            _safe_print(f"  Feedback de correcao injetado: {feedback_qualidade[:100]}...")

        _print_agente(2, "PLANEJADOR (Planner)")
        dados_agente_2 = chamar_agente(
            AGENTE_2_PLANEJADOR, entrada_planejador, PlanejadorOutput
        )
        logger.info("Agente 2 (Planejador) concluido.")
        num_passos = len(dados_agente_2.get("plano_de_acao", []))
        _safe_print(f"  Passos planejados: {num_passos}")

        _print_agente(3, "PESQUISADOR (Research)")
        contexto_repo = _ler_contexto_repositorio(max_caracteres=1000)
        entrada_pesquisador = (
            f"PLANO:\n{dados_agente_2}\n\nARQUIVOS DO PROJETO:\n{contexto_repo}"
        )
        dados_agente_3 = chamar_agente(
            AGENTE_3_PESQUISADOR, entrada_pesquisador, PesquisadorOutput
        )
        logger.info("Agente 3 (Pesquisador) concluido.")
        num_dados = len(dados_agente_3.get("dados_coletados", []))
        _safe_print(f"  Fontes coletadas: {num_dados}")

        _print_agente(4, "EXECUTOR ESPECIALISTA")
        entrada_executor = _limitar(
            f"PLANO:\n{dados_agente_2}\n\nPESQUISA:\n{dados_agente_3}", 3000
        )
        dados_agente_4 = chamar_agente(
            AGENTE_4_EXECUTOR, entrada_executor, ExecutorOutput
        )
        logger.info("Agente 4 (Executor) concluido.")
        tamanho = len(dados_agente_4.get("rascunho_da_solucao", ""))
        _safe_print(f"  Rascunho gerado: {tamanho} caracteres")

        _print_agente(5, "CONSOLIDADOR (Synthesizer)")
        entrada_consolidador = _limitar(
            f"PLANO:\n{dados_agente_2}\n\nCODIGO GERADO:\n{dados_agente_4}", 3000
        )
        dados_agente_5 = chamar_agente(
            AGENTE_5_CONSOLIDADOR, entrada_consolidador, ConsolidadorOutput
        )
        logger.info("Agente 5 (Consolidador) concluido.")
        documento_atual = dados_agente_5["documento_final_formatado"]
        _safe_print(f"  Documento formatado: {len(documento_atual)} caracteres")

        _print_agente(6, "AVALIADOR / CRITICO (QA)")
        resultado_agente_6 = chamar_agente(
            AGENTE_6_AVALIADOR, _limitar(documento_atual, 3000), AvaliadorOutput
        )
        logger.info("Agente 6 (Avaliador) concluido: %s", resultado_agente_6["status"])
        _safe_print(f"  Status: {resultado_agente_6['status']}")

        if resultado_agente_6["status"] == "REPROVADO":
            feedback_qualidade = resultado_agente_6["motivo_da_reprovacao"]
            tentativas_qualidade += 1
            logger.warning("Qualidade REPROVADO. Feedback: %s", feedback_qualidade)
            _safe_print(f"  Motivo: {feedback_qualidade[:200]}")
            continue

        _safe_print("  Qualidade APROVADO! Iniciando verificacao de seguranca...")

        resultado_final = _loop_seguranca(documento_atual)
        if resultado_final is not None:
            _print_separador("PIPELINE CONCLUIDO COM SUCESSO")
            return resultado_final

        logger.warning(
            "Loop de seguranca esgotado. Forcando reprovacao para refatoracao."
        )
        feedback_qualidade = (
            "A arquitetura proposta gera vazamento de dados ou inconformidades "
            "de seguranca insoluveis na camada de edicao."
        )
        tentativas_qualidade += 1

    mensagem = (
        "Falha na automacao. O sistema atingiu o limite maximo de "
        f"{MAX_REPROVACAO_QUALIDADE} reprocessamentos sem aprovacao.\n"
        f"Ultimo feedback: {feedback_qualidade}"
    )
    logger.error(mensagem)
    return mensagem


def _loop_seguranca(documento: str) -> str | None:
    tentativas = 0
    feedback_seguranca = ""
    documento_atual = documento

    while tentativas < MAX_REPROVACAO_SEGURANCA:
        _print_separador(
            f"CICLO DE SEGURANCA {tentativas + 1}/{MAX_REPROVACAO_SEGURANCA}"
        )

        if feedback_seguranca:
            _safe_print("  Consolidador corrigindo por seguranca...")
            entrada_consolidador = _limitar(
                f"DOCUMENTO ATUAL:\n{documento_atual}\n\n"
                f"FEEDBACK DE SEGURANCA:\n{feedback_seguranca}",
                3000,
            )
            resultado_refeito = chamar_agente(
                AGENTE_5_REFAZ_POR_SEGURANCA, entrada_consolidador, ConsolidadorOutput
            )
            documento_atual = resultado_refeito["documento_final_formatado"]
            logger.info("Consolidador refez o documento por seguranca.")

        _print_agente(7, "GUARDIAO DE SEGURANCA (Guardrail)")
        resultado_agente_7 = chamar_agente(
            AGENTE_7_GUARDIAO, _limitar(documento_atual, 3000), GuardiaoOutput
        )
        logger.info(
            "Agente 7 (Guardiao) concluido: %s",
            resultado_agente_7["status_seguranca"],
        )
        _safe_print(f"  Status: {resultado_agente_7['status_seguranca']}")

        if resultado_agente_7["status_seguranca"] == "SEGURO":
            logger.info("Documento 100% aprovado em qualidade e seguranca!")
            _safe_print("  Documento SEGURO. Liberado para o usuario!")
            return resultado_agente_7["resposta_final_higienizada"]

        politica = resultado_agente_7.get("politica_violada", "desconhecida")
        _safe_print(f"  Politica violada: {politica}")
        feedback_seguranca = _limitar(
            f"CORRECAO DE SEGURANCA: {politica}. "
            f"Detalhes: {resultado_agente_7['resposta_final_higienizada']}. "
            f"Remova ou reescreva o trecho violador.",
            2000,
        )
        logger.warning("Seguranca BLOQUEADO: %s", politica)
        tentativas += 1

    _safe_print("  Limite de seguranca atingido. Retornando ao ciclo de qualidade.")
    return None
