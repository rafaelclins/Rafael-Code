import argparse
import logging
import os
import re
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from config import APP_VERSION, LOG_LEVEL, ZEN_API_URL, ZEN_MODEL, ZEN_TIMEOUT
from file_manager import FileManager, extrair_arquivos_do_texto
from orquestrador import PipelineResult, conversar_gerente, executar_pipeline
from utils.formatador import exibir_resposta_agente, limpar_texto

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("main")

console = Console()

_RE_BLOCO_CODIGO = re.compile(r"```([\w+-]*)\s*\n(.*?)```", re.DOTALL)

_LINGUAGENS_PYTHON = {"python", "py", "python3", "python3.12"}

_MODO = "PLAN"

_tab_bindings = KeyBindings()


@_tab_bindings.add(Keys.Tab)
def _alternar_modo(event) -> None:
    global _MODO
    _MODO = "BUILD" if _MODO == "PLAN" else "PLAN"
    event.app.invalidate()


_prompt_session: PromptSession | None = None


def _modo_prompt():
    if _MODO == "PLAN":
        return HTML("<b><green>[PLAN]</green></b> > ")
    return HTML("<b><yellow>[BUILD]</yellow></b> > ")


def _modo_toolbar():
    if _MODO == "PLAN":
        return HTML(
            "<green>PLAN</green> — converse livremente com o Gerente.  "
            "<i>TAB alterna o modo</i>"
        )
    return HTML(
        "<yellow>BUILD</yellow> — <b>Enter</b> dispara a esteira A1→A7.  "
        "<i>TAB alterna o modo</i>"
    )


def _ler_entrada() -> str:
    global _prompt_session
    if _prompt_session is None:
        _prompt_session = PromptSession()
    return _prompt_session.prompt(
        _modo_prompt,
        key_bindings=_tab_bindings,
        bottom_toolbar=_modo_toolbar,
    )


def exibir_cabecalho() -> None:
    tabela = Table(show_header=False, box=None, padding=(0, 1))
    tabela.add_column("Atributo", style="bold cyan", no_wrap=True)
    tabela.add_column("Valor", style="white")
    tabela.add_row("Versão", f"v{APP_VERSION}")
    tabela.add_row("Modelo", ZEN_MODEL)
    tabela.add_row("URL", ZEN_API_URL)
    tabela.add_row("Diretório ativo", os.getcwd())
    tabela.add_row("Timeout", f"connect=30s, read={ZEN_TIMEOUT}s")

    painel = Panel(
        tabela,
        title="[bold magenta]RAFAEL CODE - Multi-Agente (7 Agentes)[/]",
        subtitle="[cyan]Pipeline com duplo loop de correção[/]",
        border_style="magenta",
        padding=(1, 2),
    )
    console.print(painel)


def _renderizar_markdown(texto: str) -> None:
    try:
        console.print(Markdown(texto))
    except Exception:
        console.print(texto)


def _exibir_resultado_final(texto: str) -> None:
    texto = limpar_texto(texto)
    console.print(Panel("[bold green]RESULTADO FINAL[/]", border_style="green"))

    if not texto:
        console.print("[dim](sem conteúdo)[/]")
        return

    tem_bloco_codigo = bool(_RE_BLOCO_CODIGO.search(texto))
    if not tem_bloco_codigo:
        exibir_resposta_agente("Consolidador", texto)
        return

    ultimo_fim = 0
    for match in _RE_BLOCO_CODIGO.finditer(texto):
        trecho_prosa = texto[ultimo_fim:match.start()]
        if trecho_prosa.strip():
            _renderizar_markdown(trecho_prosa)

        linguagem = match.group(1) or "text"
        if linguagem.lower() in _LINGUAGENS_PYTHON:
            linguagem = "python"

        bloco = Syntax(
            match.group(2).strip("\n"),
            linguagem,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        console.print(bloco)
        ultimo_fim = match.end()

    trecho_final = texto[ultimo_fim:]
    if trecho_final.strip():
        _renderizar_markdown(trecho_final)


def exemplo_interativo(diretorio: str | None = None) -> PipelineResult | None:
    global _MODO
    if diretorio:
        os.chdir(diretorio)
        logger.info("Diretório de trabalho alterado para: %s", diretorio)

    exibir_cabecalho()

    historico: list[str] = []
    ultimo_resultado: PipelineResult | None = None
    primeira_mensagem = True

    while True:
        try:
            texto = _ler_entrada().strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Até logo![/]")
            break

        if not texto and primeira_mensagem:
            texto = (
                "Preciso criar um portifolio React + Tailwind CSS hospedado "
                "com custo zero real, sem cartao de credito, com HTTPS e "
                "deploy automatico via Git."
            )
            console.print(f"[dim]Usando exemplo:[/] {texto}")
        primeira_mensagem = False

        if _MODO == "PLAN":
            if not texto:
                continue
            historico.append(f"Usuário: {texto}")
            console.print("\n[bold green]Gerente:[/] pensando...")
            resposta = conversar_gerente(texto, historico)
            historico.append(f"Gerente: {resposta}")
            console.print(
                Panel(
                    Markdown(resposta),
                    title="[bold green]Gerente (PLAN)[/]",
                    border_style="green",
                )
            )
        else:
            pedido_build = texto or "Executar o plano desenvolvido na conversa."
            if texto:
                historico.append(f"Usuário: {texto}")
            contexto = "\n\n".join(historico)
            console.print(
                "\n[bold yellow]>>> Modo BUILD: disparando a esteira A1 → A7 <<<[/]\n"
            )
            ultimo_resultado = executar_pipeline(
                pedido_build, contexto_conversa=contexto
            )
            _exibir_resultado_final(ultimo_resultado.text)
            if not ultimo_resultado.success:
                console.print(
                    "[red]Pipeline falhou.[/] Volte a conversar para ajustar o plano."
                )
            historico.append(
                f"Sistema: BUILD {'OK' if ultimo_resultado.success else 'FALHOU'}"
            )
            _MODO = "PLAN"
            console.print(
                "[dim]Modo voltou para [green]PLAN[/]. "
                "Pressione TAB para BUILD novamente.[/]\n"
            )

    return ultimo_resultado


def _gravar_arquivos(resultado: PipelineResult, confirmar: bool) -> bool:
    if not resultado.success:
        return True

    arquivos = list(resultado.arquivos)
    if not arquivos:
        arquivos = extrair_arquivos_do_texto(resultado.text)

    if not arquivos:
        tabela = Table(title="RELATÓRIO DE ALTERAÇÕES NO HD", border_style="cyan")
        tabela.add_column("Caminho")
        tabela.add_column("Status")
        tabela.add_row("(nenhum arquivo detectado para gravação)", "-")
        console.print(tabela)
        return True

    if confirmar:
        resposta = console.input(
            "\n[bold yellow]Deseja confirmar a gravação no HD?[/] [dim](S/n):[/] "
        ).strip().lower()
        if resposta not in ("s", "sim", ""):
            console.print("[yellow]Gravação cancelada pelo usuário.[/]")
            return True

    fm = FileManager()
    relatorio = fm.aplicar_alteracoes(arquivos)

    tabela = Table(title="RELATÓRIO DE ALTERAÇÕES NO HD", border_style="cyan")
    tabela.add_column("Caminho")
    tabela.add_column("Status")
    tabela.add_column("Ação")
    tabela.add_column("Backup / Detalhe")
    for item in relatorio:
        status = "[bold green]OK[/]" if item["status"] == "OK" else "[bold red]ERRO[/]"
        acao = item["acao"].upper()
        caminho = item["caminho"] or "(vazio)"
        obs = item.get("backup") or item.get("detalhe") or ""
        tabela.add_row(caminho, status, acao, obs)
    console.print(tabela)

    return all(item["status"] == "OK" for item in relatorio)


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
    parser.add_argument(
        "--criar",
        action="store_true",
        help="Grava no HD os arquivos aprovados pelos agentes (com backup em .rafael_backups).",
    )
    args = parser.parse_args()

    if args.version:
        console.print(f"Rafael Code v{APP_VERSION}")
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
        gravacao_ok = True
        if args.criar:
            gravacao_ok = _gravar_arquivos(resultado, confirmar=False)
        sys.exit(0 if (resultado.success and gravacao_ok) else 1)
    else:
        resultado = exemplo_interativo(diretorio=args.diretorio)
        gravacao_ok = True
        if resultado is not None and args.criar:
            gravacao_ok = _gravar_arquivos(resultado, confirmar=True)
        sucesso = resultado is not None and resultado.success and gravacao_ok
        sys.exit(0 if sucesso else 1)
