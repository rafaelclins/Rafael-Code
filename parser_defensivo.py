import json
import re
from typing import Any, Dict


def extrair_json_por_profundidade(texto: str) -> Dict[str, Any]:
    stack = []
    start = None
    for i, ch in enumerate(texto):
        if ch == "{":
            if not stack:
                start = i
            stack.append(i)
        elif ch == "}":
            stack.pop()
            if not stack and start is not None:
                try:
                    return json.loads(texto[start : i + 1])
                except json.JSONDecodeError:
                    raise ValueError("JSON aninhado encontrado, mas com sintaxe invalida.")
    raise ValueError("Nenhum bloco JSON valido foi encontrado no texto.")


def extrair_json_com_regex(texto: str) -> Dict[str, Any]:
    padrao = re.search(r"(\{.*\})", texto, re.DOTALL)
    if padrao:
        try:
            return json.loads(padrao.group(1))
        except json.JSONDecodeError:
            pass
    raise ValueError("Nenhum bloco JSON {} encontrado via regex.")


def extrair_e_validar_json(texto_bruto: str) -> Dict[str, Any]:
    texto = texto_bruto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    try:
        return extrair_json_por_profundidade(texto)
    except ValueError:
        pass

    try:
        return extrair_json_com_regex(texto)
    except ValueError:
        pass

    raise ValueError(
        "Falha ao extrair JSON. O modelo nao retornou um JSON valido em nenhum formato esperado."
    )
