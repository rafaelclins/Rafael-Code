import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PASTAS_IGNORADAS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".rafael_backups",
    ".github",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".history",
    "node_modules",
}

MAX_CARACTERES = 8000


def _eh_pasta_ignorada(nome: str) -> bool:
    return nome in PASTAS_IGNORADAS or nome.startswith(".")


def _docstring_resumo(node) -> str:
    doc = ast.get_docstring(node, clean=False)
    if not doc:
        return ""
    primeira_linha = doc.strip().splitlines()[0].strip()
    return primeira_linha[:120]


def _eh_funcao(node) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


def _assinar_funcao(node) -> str:
    prefixo = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    try:
        parametros = ast.unparse(node.args)
    except Exception:
        parametros = ""
    linha = f"{prefixo} {node.name}({parametros})"
    doc = _docstring_resumo(node)
    if doc:
        linha += f"  # {doc}"
    return linha


def _resumo_arquivo(caminho: Path, relativo: Path) -> str:
    try:
        conteudo = caminho.read_text(encoding="utf-8-sig")
        arvore = ast.parse(conteudo)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
        logger.warning("Scanner AST ignorou arquivo inválido: %s", relativo)
        return ""

    linhas: list[str] = [f"### `{relativo}`"]
    for node in arvore.body:
        if isinstance(node, ast.ClassDef):
            try:
                bases = ast.unparse(node.bases) if node.bases else ""
            except Exception:
                bases = ""
            titulo = f"class {node.name}{bases}"
            doc = _docstring_resumo(node)
            if doc:
                titulo += f"  # {doc}"
            linhas.append(f"- {titulo}")
            for item in node.body:
                if _eh_funcao(item):
                    linhas.append(f"  - {_assinar_funcao(item)}")
        elif _eh_funcao(node):
            linhas.append(f"- {_assinar_funcao(node)}")

    if len(linhas) == 1:
        return ""
    return "\n".join(linhas)


def escanear_repositorio(root_dir: str = ".") -> str:
    root = Path(root_dir)
    if not root.is_dir():
        logger.warning("Diretório de varredura inválido: %s", root)
        return "# Mapa do Repositório (Scanner AST)\n\n(diretório inválido ou não encontrado)"

    linhas: list[str] = ["# Mapa do Repositório (Scanner AST)", ""]
    arquivos_no_mapa = 0

    for caminho in sorted(root.rglob("*.py")):
        try:
            relativo = caminho.relative_to(root)
        except ValueError:
            continue
        if any(_eh_pasta_ignorada(parte) for parte in relativo.parts[:-1]):
            continue
        resumo = _resumo_arquivo(caminho, relativo)
        if resumo:
            linhas.append(resumo)
            linhas.append("")
            arquivos_no_mapa += 1
        if sum(len(linha) for linha in linhas) > MAX_CARACTERES:
            linhas.append("*...(mapa do repositório truncado por tamanho)*")
            break

    if arquivos_no_mapa == 0:
        return (
            "# Mapa do Repositório (Scanner AST)\n\n"
            "(nenhum arquivo .py relevante encontrado)"
        )

    texto = "\n".join(linhas).strip()
    if len(texto) > MAX_CARACTERES:
        texto = texto[:MAX_CARACTERES] + "\n\n*...[TRUNCADO]"
    return texto
