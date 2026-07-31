from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def limpar_texto(texto: str) -> str:
    """Remove espaços extras no início, fim e linhas em branco."""
    if not texto:
        return ""
    return texto.strip()


def formatar_resposta_agente(nome_agente: str, resposta: str) -> str:
    """Formata a saída de um agente para exibição limpa no terminal."""
    separador = "=" * 40
    return f"\n{separador}\n🤖 Agente: {nome_agente}\n{separador}\n{resposta.strip()}\n"


def formatar_fase(fase: str, titulo: str, conteudo: str) -> str:
    """Formata uma fase do pipeline (ex.: [PLAN], [BUILD]) para exibição clara."""
    separador = "=" * 40
    return f"\n{separador}\n{fase} - {titulo}\n{separador}\n{conteudo.strip()}\n"


_console: Console | None = None


def _obter_console() -> Console:
    global _console
    if _console is None:
        _console = Console()
    return _console


def _print_fallback(texto: str) -> None:
    try:
        print(texto)
    except UnicodeEncodeError:
        print(ascii(texto)[1:-1])


def exibir_resposta_agente(nome_agente: str, resposta: str) -> None:
    """Exibe a resposta de um agente em um painel Rich com Markdown renderizado."""
    texto = limpar_texto(resposta)
    try:
        _obter_console().print(
            Panel(
                Markdown(texto),
                title=f"[bold cyan]🤖 {nome_agente}[/]",
                border_style="cyan",
            )
        )
    except Exception:
        _print_fallback(formatar_resposta_agente(nome_agente, texto))


def exibir_fase(fase: str, titulo: str, conteudo: str) -> None:
    """Exibe uma fase do pipeline em um painel Rich com Markdown renderizado."""
    texto = limpar_texto(conteudo)
    try:
        _obter_console().print(
            Panel(
                Markdown(texto),
                title=f"[bold yellow]{fase} - {titulo}[/]",
                border_style="yellow",
            )
        )
    except Exception:
        _print_fallback(formatar_fase(fase, titulo, texto))
