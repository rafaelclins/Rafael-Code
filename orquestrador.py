import logging
import sys
from dataclasses import dataclass, field

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
from database import (
    criar_sessao,
    init_db,
    salvar_log_agente,
    ultimos_pedidos,
)
from ollama_client import ErroModelo, chamar_agente
from repo_scanner import escanear_repositorio
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


@dataclass
class PipelineResult:
    text: str
    success: bool
    arquivos: list = field(default_factory=list)


@dataclass
class ResultadoPipeline:
    texto: str
    arquivos: list = field(default_factory=list)


def _safe_print_err(texto: str) -> None:
    try:
        print(texto, file=sys.stderr)
    except UnicodeEncodeError:
        print(repr(texto)[1:-1], file=sys.stderr)


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


def executar_pipeline(pedido_usuario: str, headless: bool = False) -> PipelineResult:
    try:
        res = _executar_pipeline_interno(pedido_usuario, headless)
        if res.texto.startswith("Falha na automação"):
            return PipelineResult(text=res.texto, success=False, arquivos=res.arquivos)
        return PipelineResult(text=res.texto, success=True, arquivos=res.arquivos)
    except ErroModelo as e:
        msg = f"Erro na API Zen: {e.mensagem}"
        logger.error(msg)
        _safe_print_err("")
        _safe_print_err(f"  ERRO: {msg}")
        return PipelineResult(text=msg, success=False)


def _executar_pipeline_interno(pedido_usuario: str, headless: bool = False) -> ResultadoPipeline:
    _print_separador("ORQUESTRADOR MULTI-AGENTE INICIADO")
    _safe_print(f"  Pedido: {pedido_usuario[:80]}{'...' if len(pedido_usuario) > 80 else ''}")
    logger.info("Iniciando pipeline multi-agente para o pedido do usuário.")

    init_db()
    historico = ultimos_pedidos(limite=2)
    sessao_id = criar_sessao(pedido_usuario)
    if historico:
        ctx = "\n".join(
            f"Historico da conversa anterior ({i+1}): {p}"
            for i, p in enumerate(historico)
        )
        entrada_alinhador = f"{ctx}\n\nNovo pedido do usuário: {pedido_usuario}"
        _safe_print(f"  Contexto histórico injetado: {len(historico)} sessão(ões) anterior(es)")
    else:
        entrada_alinhador = pedido_usuario

    _print_agente(1, "ALINHADOR (Orchestrator)")
    dados_agente_1 = chamar_agente(
        AGENTE_1_ALINHADOR, entrada_alinhador, AlinhadorOutput
    )
    salvar_log_agente(sessao_id, "Alinhador", str(dados_agente_1))
    logger.info("Agente 1 (Alinhador) concluído.")
    _safe_print(f"  Objetivo: {dados_agente_1.get('objetivo_principal', 'N/A')[:100]}")

    mapa_repositorio = escanear_repositorio()
    _safe_print(
        f"  Mapa do repositório (Scanner AST) carregado: {len(mapa_repositorio)} caracteres"
    )

    tentativas_qualidade = 0
    feedback_qualidade = ""

    while tentativas_qualidade < MAX_REPROVACAO_QUALIDADE:
        _print_separador(
            f"CICLO DE QUALIDADE {tentativas_qualidade + 1}/{MAX_REPROVACAO_QUALIDADE}"
        )

        entrada_planejador = _limitar(str(dados_agente_1), 2000)
        if feedback_qualidade:
            entrada_planejador += (
                f"\n[CORREÇÃO OBRIGATÓRIA]: O avaliador reprovou o ciclo anterior "
                f"pelo motivo: {feedback_qualidade}"
            )
            entrada_planejador = _limitar(entrada_planejador, 2500)
            _safe_print(f"  Feedback de correção injetado: {feedback_qualidade[:100]}...")

        _print_agente(2, "PLANEJADOR (Planner)")
        try:
            dados_agente_2 = chamar_agente(
                AGENTE_2_PLANEJADOR, entrada_planejador, PlanejadorOutput
            )
            salvar_log_agente(sessao_id, "Planejador", str(dados_agente_2))
            logger.info("Agente 2 (Planejador) concluído.")
            num_passos = len(dados_agente_2.get("plano_de_acao", []))
            _safe_print(f"  Passos planejados: {num_passos}")
        except ErroModelo as e:
            num_passos = 0
            _safe_print_err(f"  A2 falhou: {e.mensagem[:80]}")

        if num_passos == 0:
            feedback_qualidade = "Planejador não gerou um plano válido."
            tentativas_qualidade += 1
            continue

        _print_agente(3, "PESQUISADOR (Research)")
        entrada_pesquisador = _limitar(
            f"PLANO:\n{dados_agente_2}\n\nMAPA DO REPOSITORIO:\n{mapa_repositorio}", 4000
        )
        try:
            dados_agente_3 = chamar_agente(
                AGENTE_3_PESQUISADOR, entrada_pesquisador, PesquisadorOutput
            )
            salvar_log_agente(sessao_id, "Pesquisador", str(dados_agente_3))
            logger.info("Agente 3 (Pesquisador) concluído.")
            num_dados = len(dados_agente_3.get("dados_coletados", []))
            _safe_print(f"  Fontes coletadas: {num_dados}")
        except ErroModelo as e:
            dados_agente_3 = {"dados_coletados": []}
            _safe_print_err(f"  A3 falhou: {e.mensagem[:80]}")

        _print_agente(4, "EXECUTOR ESPECIALISTA")
        entrada_executor = _limitar(
            f"PLANO:\n{dados_agente_2}\n\nPESQUISA:\n{dados_agente_3}\n\n"
            f"MAPA DO REPOSITORIO:\n{mapa_repositorio}",
            5000,
        )
        try:
            dados_agente_4 = chamar_agente(
                AGENTE_4_EXECUTOR, entrada_executor, ExecutorOutput
            )
            salvar_log_agente(sessao_id, "Executor", str(dados_agente_4))
            logger.info("Agente 4 (Executor) concluído.")
            tamanho = len(dados_agente_4.get("rascunho_da_solucao", ""))
            _safe_print(f"  Rascunho gerado: {tamanho} caracteres")
        except ErroModelo as e:
            _safe_print_err(f"  A4 falhou: {e.mensagem[:80]}")
            feedback_qualidade = "Executor não conseguiu gerar código."
            tentativas_qualidade += 1
            continue

        _print_agente(5, "CONSOLIDADOR (Synthesizer)")
        entrada_consolidador = _limitar(
            f"PLANO:\n{dados_agente_2}\n\nCODIGO:\n{dados_agente_4}", 800
        )
        try:
            dados_agente_5 = chamar_agente(
                AGENTE_5_CONSOLIDADOR, entrada_consolidador, ConsolidadorOutput
            )
            salvar_log_agente(sessao_id, "Consolidador", str(dados_agente_5))
            logger.info("Agente 5 (Consolidador) concluído.")
            documento_atual = dados_agente_5["documento_final_formatado"]
            arquivos = dados_agente_5.get("arquivos", [])
            _safe_print(f"  Documento formatado: {len(documento_atual)} caracteres")
            _safe_print(f"  Arquivos propostos: {len(arquivos)}")
        except ErroModelo as e:
            _safe_print_err(f"  A5 falhou: {e.mensagem[:80]}")
            feedback_qualidade = "Consolidador não conseguiu formatar a saída."
            tentativas_qualidade += 1
            continue

        _print_agente(6, "AVALIADOR / CRITICO (QA)")
        try:
            resultado_agente_6 = chamar_agente(
                AGENTE_6_AVALIADOR, _limitar(documento_atual, 1500), AvaliadorOutput
            )
            salvar_log_agente(sessao_id, "Avaliador", str(resultado_agente_6))
            logger.info("Agente 6 (Avaliador) concluído: %s", resultado_agente_6["status"])
            _safe_print(f"  Status: {resultado_agente_6['status']}")
        except ErroModelo as e:
            _safe_print_err(f"  A6 falhou: {e.mensagem[:80]}")
            feedback_qualidade = "Avaliador não conseguiu avaliar."
            tentativas_qualidade += 1
            continue

        if resultado_agente_6["status"] == "REPROVADO":
            feedback_qualidade = resultado_agente_6["motivo_da_reprovacao"]
            logger.warning("Qualidade REPROVADO. Feedback: %s", feedback_qualidade)
            _safe_print(f"  Motivo: {feedback_qualidade[:200]}")
            if headless:
                return ResultadoPipeline(
                    f"Falha na automação. Agente 6 (Avaliador) reprovou: {feedback_qualidade}"
                )
            tentativas_qualidade += 1
            continue

        _safe_print("  Qualidade APROVADO! Iniciando verificação de segurança...")

        resultado_final = _loop_seguranca(documento_atual, sessao_id, headless, arquivos)
        if resultado_final is not None:
            _print_separador("PIPELINE CONCLUIDO COM SUCESSO")
            return resultado_final

        logger.warning(
            "Loop de segurança esgotado. Forçando reprovação para refatoração."
        )
        feedback_qualidade = (
            "A arquitetura proposta gera vazamento de dados ou inconformidades "
            "de segurança insolúveis na camada de edição."
        )
        tentativas_qualidade += 1

    mensagem = (
        "Falha na automação. O sistema atingiu o limite máximo de "
        f"{MAX_REPROVACAO_QUALIDADE} reprocessamentos sem aprovação.\n"
        f"Último feedback: {feedback_qualidade}"
    )
    logger.error(mensagem)
    return ResultadoPipeline(mensagem)


def _loop_seguranca(
    documento: str,
    sessao_id: int,
    headless: bool = False,
    arquivos: list | None = None,
) -> ResultadoPipeline | None:
    tentativas = 0
    feedback_seguranca = ""
    documento_atual = documento
    documento_limitado = _limitar(documento, 1500)
    if arquivos is None:
        arquivos = []

    while tentativas < MAX_REPROVACAO_SEGURANCA:
        _print_separador(
            f"CICLO DE SEGURANÇA {tentativas + 1}/{MAX_REPROVACAO_SEGURANCA}"
        )

        if feedback_seguranca:
            _safe_print("  Consolidador corrigindo por segurança...")
            entrada_consolidador = _limitar(
                f"DOCUMENTO ATUAL:\n{documento_atual}\n\n"
                f"FEEDBACK DE SEGURANÇA:\n{feedback_seguranca}",
                1500,
            )
            try:
                resultado_refeito = chamar_agente(
                    AGENTE_5_REFAZ_POR_SEGURANCA, entrada_consolidador, ConsolidadorOutput
                )
                salvar_log_agente(sessao_id, "Consolidador_Refaz", str(resultado_refeito))
                documento_atual = resultado_refeito["documento_final_formatado"]
                documento_limitado = _limitar(documento_atual, 1500)
                novos_arquivos = resultado_refeito.get("arquivos")
                if novos_arquivos:
                    arquivos = novos_arquivos
                logger.info("Consolidador refez o documento por segurança.")
            except ErroModelo:
                _safe_print_err("  A5 (refaz) falhou. Seguindo com o documento atual.")

        _print_agente(7, "GUARDIÃO DE SEGURANÇA (Guardrail)")
        try:
            resultado_agente_7 = chamar_agente(
                AGENTE_7_GUARDIAO, documento_limitado, GuardiaoOutput
            )
            salvar_log_agente(sessao_id, "Guardiao", str(resultado_agente_7))
            logger.info(
                "Agente 7 (Guardião) concluído: %s",
                resultado_agente_7["status_seguranca"],
            )
            _safe_print(f"  Status: {resultado_agente_7['status_seguranca']}")

            if resultado_agente_7["status_seguranca"] == "SEGURO":
                logger.info("Documento 100% aprovado em qualidade e segurança!")
                _safe_print("  Documento SEGURO. Liberado para o usuário!")
                return ResultadoPipeline(
                    resultado_agente_7["resposta_final_higienizada"], arquivos
                )

            politica = resultado_agente_7.get("politica_violada", "desconhecida")
            _safe_print(f"  Política violada: {politica}")
            if headless:
                return ResultadoPipeline(
                    f"Falha na automação. Agente 7 (Guardião) bloqueou: {politica}"
                )
            feedback_seguranca = _limitar(
                f"CORREÇÃO DE SEGURANÇA: {politica}. "
                f"Detalhes: {resultado_agente_7['resposta_final_higienizada']}. "
                f"Remova ou reescreva o trecho violador.",
                1000,
            )
            logger.warning("Segurança BLOQUEADO: %s", politica)
        except ErroModelo:
            _safe_print_err("  A7 falhou. Seguindo para o próximo ciclo.")
            feedback_seguranca = "Guardião não respondeu. Refazendo por segurança."

        tentativas += 1

    _safe_print("  Limite de segurança atingido. Retornando ao ciclo de qualidade.")
    return None
