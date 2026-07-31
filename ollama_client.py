import json
import logging
import re
import sys
import threading
import time
import unicodedata
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    ZEN_API_KEY,
    ZEN_API_URL,
    ZEN_MODEL,
    ZEN_TIMEOUT,
    TEMPERATURA_INCREMENTO,
    TEMPERATURA_INICIAL,
    MAX_TENTATIVAS_MODELO,
)
from parser_defensivo import extrair_e_validar_json

logger = logging.getLogger(__name__)

VERBOSE_MODE = False
HEADLESS_MODE = False


class ErroModelo(Exception):
    def __init__(self, mensagem: str, tentativa: int = 0):
        self.mensagem = mensagem
        self.tentativa = tentativa
        super().__init__(mensagem)


def criar_sessao() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=2,
        read=0,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"Content-Type": "application/json"})
    if ZEN_API_KEY:
        session.headers.update({"Authorization": f"Bearer {ZEN_API_KEY}"})
    return session


def _extrair_texto(data: dict) -> str:
    output = data.get("output") or []
    if output:
        conteudos = output[0].get("content") or []
        if conteudos:
            return conteudos[0].get("text", "")

    choices = data.get("choices") or []
    if choices:
        return (choices[0].get("message") or {}).get("content", "")

    return ""


def _agente_mensagem(agente: str) -> str:
    if agente in ("Executor", "Consolidador"):
        return "Pensando e gerando a solução técnica..."
    if agente in ("Alinhador", "Planejador"):
        return "Estruturando os passos e objetivos..."
    if agente == "Pesquisador":
        return "Pesquisando contexto no repositório..."
    if agente in ("Avaliador", "Guardiao"):
        return "Validando qualidade e segurança do código..."
    return "Aguardando resposta do modelo..."


def _log_progress(modelo: str, tentativa: int, total: int, stop: threading.Event, agente: str = "") -> None:
    if HEADLESS_MODE:
        return
    spinner = r"-\|/"
    i = 0
    start = time.monotonic()
    mensagem = _agente_mensagem(agente)
    while not stop.wait(timeout=0.2):
        elapsed = int(time.monotonic() - start)
        i = (i + 1) % 4
        sys.stdout.write(f"\r  {spinner[i]} {mensagem} ({elapsed}s)")
        sys.stdout.flush()
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


def _enviar_e_extrair(
    sessao: requests.Session,
    payload: dict,
    modelo: str,
    tentativa: int,
    total: int,
    agente: str = "",
) -> str:
    stop = threading.Event()
    t = threading.Thread(
        target=_log_progress, args=(modelo, tentativa, total, stop, agente), daemon=True,
    )
    t.start()
    try:
        resp = sessao.post(ZEN_API_URL, json=payload, timeout=(30, 600))
        resp.raise_for_status()
        raw = resp.json()
        if not isinstance(raw, dict):
            raise ValueError(f"Resposta não é dict: {type(raw).__name__}")
        return _extrair_texto(raw)
    finally:
        stop.set()


def chamar_conversa(
    prompt_sistema: str,
    historico: list[dict],
    entrada_usuario: str,
    temperatura: Optional[float] = None,
) -> str:
    """Chat livre (sem schema JSON). Retorna o texto bruto do modelo."""
    if temperatura is None:
        temperatura = TEMPERATURA_INICIAL
    sessao = criar_sessao()
    mensagens: list[dict] = [{"role": "system", "content": prompt_sistema}]
    mensagens.extend(historico or [])
    mensagens.append({"role": "user", "content": entrada_usuario})

    for tentativa in range(MAX_TENTATIVAS_MODELO):
        temp_atual = temperatura + (tentativa * TEMPERATURA_INCREMENTO)
        try:
            payload = {
                "model": ZEN_MODEL,
                "messages": mensagens,
                "temperature": temp_atual,
                "max_tokens": 16384,
            }
            if VERBOSE_MODE:
                logger.info(
                    "--- PAYLOAD CHAT ---\n%s",
                    json.dumps(payload, indent=2, ensure_ascii=False),
                )
            texto_resposta = _enviar_e_extrair(
                sessao, payload, ZEN_MODEL, tentativa + 1, MAX_TENTATIVAS_MODELO
            )
            if texto_resposta:
                if VERBOSE_MODE:
                    logger.info("--- RESPOSTA CHAT ---\n%s", texto_resposta)
                return texto_resposta
            logger.warning("Resposta vazia no chat. Auto-retry com temperature=0.2...")
            payload["temperature"] = 0.2
            texto_resposta = _enviar_e_extrair(
                sessao, payload, ZEN_MODEL, tentativa + 1, MAX_TENTATIVAS_MODELO
            )
            if texto_resposta:
                return texto_resposta
            raise ValueError("Resposta vazia da API Zen no chat")
        except requests.Timeout:
            logger.warning("Timeout no chat (tentativa %d).", tentativa + 1)
            if tentativa < MAX_TENTATIVAS_MODELO - 1:
                time.sleep(2 ** tentativa)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            logger.warning("HTTP %s no chat: %s", status, e)
            if status in (400, 401, 404):
                raise ErroModelo(
                    f"API Zen retornou {status} no chat. "
                    f"Verifique a URL '{ZEN_API_URL}' e a chave de API.",
                    tentativa,
                )
            if tentativa < MAX_TENTATIVAS_MODELO - 1:
                time.sleep(2 ** tentativa)
        except requests.RequestException as e:
            logger.warning("Erro de requisição no chat: %s", e)
            if tentativa < MAX_TENTATIVAS_MODELO - 1:
                time.sleep(2 ** tentativa)
        except ValueError as e:
            logger.warning("Erro de processamento no chat: %s", e)
            if tentativa < MAX_TENTATIVAS_MODELO - 1:
                time.sleep(2 ** tentativa)

    raise ErroModelo(
        f"Falha após {MAX_TENTATIVAS_MODELO} tentativas no chat.",
        MAX_TENTATIVAS_MODELO - 1,
    )


def _detectar_agente(prompt: str) -> str:
    prompt_normalizado = unicodedata.normalize(
        "NFKD", prompt.lower()
    ).encode("ascii", "ignore").decode("ascii")
    correspondencia = re.search(r"voce e o agente ([1-7])", prompt_normalizado)
    if correspondencia:
        numeros_para_nomes = {
            1: "Alinhador",
            2: "Planejador",
            3: "Pesquisador",
            4: "Executor",
            5: "Consolidador",
            6: "Avaliador",
            7: "Guardiao",
        }
        return numeros_para_nomes[int(correspondencia.group(1))]
    if "alinhador" in prompt_normalizado:
        return "Alinhador"
    if "planejador" in prompt_normalizado or "planner" in prompt_normalizado:
        return "Planejador"
    if "pesquisador" in prompt_normalizado:
        return "Pesquisador"
    if "executor" in prompt_normalizado or "builder" in prompt_normalizado:
        return "Executor"
    if "consolidador" in prompt_normalizado:
        return "Consolidador"
    if "avaliador" in prompt_normalizado or "critico" in prompt_normalizado:
        return "Avaliador"
    if "guardiao" in prompt_normalizado or "guardrail" in prompt_normalizado:
        return "Guardiao"
    return ""


def chamar_agente(
    prompt_sistema: str,
    entrada_usuario: str,
    esquema_pydantic: Any,
    max_tentativas: Optional[int] = None,
    temperatura: Optional[float] = None,
) -> Dict[str, Any]:
    if max_tentativas is None:
        max_tentativas = MAX_TENTATIVAS_MODELO
    if temperatura is None:
        temperatura = TEMPERATURA_INICIAL

    nome_agente = _detectar_agente(prompt_sistema)
    sessao = criar_sessao()
    ultimo_erro = ""

    for tentativa in range(max_tentativas):
        temp_atual = temperatura + (tentativa * TEMPERATURA_INCREMENTO)
        logger.info(
            "Agente chamado | tentativa %d/%d | temp=%.2f | modelo=%s",
            tentativa + 1, max_tentativas, temp_atual, ZEN_MODEL,
        )

        try:
            payload = {
                "model": ZEN_MODEL,
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Dados de Entrada:\n{entrada_usuario}"},
                ],
                "temperature": temp_atual,
                "max_tokens": 16384,
            }

            if VERBOSE_MODE:
                logger.info(
                    "--- PAYLOAD ENVIADO ---\n%s",
                    json.dumps(payload, indent=2, ensure_ascii=False),
                )

            texto_resposta = _enviar_e_extrair(
                sessao, payload, ZEN_MODEL, tentativa + 1, max_tentativas, agente=nome_agente,
            )

            if not texto_resposta:
                logger.warning(
                    "Resposta vazia. Auto-retry com temperature=0.2..."
                )
                payload["temperature"] = 0.2
                texto_resposta = _enviar_e_extrair(
                    sessao, payload, ZEN_MODEL, tentativa + 1, max_tentativas, agente=nome_agente,
                )

            if not texto_resposta:
                raise ValueError("Resposta vazia da API Zen (mesmo após auto-retry)")

            if VERBOSE_MODE:
                logger.info(
                    "--- RESPOSTA RECEBIDA ---\n%s",
                    texto_resposta,
                )

            dados_validados = extrair_e_validar_json(texto_resposta)
            esquema_pydantic(**dados_validados)
            return dados_validados

        except requests.Timeout:
            ultimo_erro = f"Timeout na tentativa {tentativa + 1}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            ultimo_erro = f"HTTP {status} na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if status in (400, 404):
                raise ErroModelo(
                    f"API Zen retornou {status}. Verifique a URL '{ZEN_API_URL}' "
                    f"e a chave de API. Detalhe: {e}",
                    tentativa,
                )
            if status == 401:
                raise ErroModelo(
                    "API Zen retornou 401 (Não Autorizado). "
                    "Verifique se a variável OPENCODE_ZEN_KEY está definida corretamente.",
                    tentativa,
                )
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except requests.RequestException as e:
            ultimo_erro = f"Erro de requisição na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except (ValueError, KeyError, IndexError, TypeError) as e:
            ultimo_erro = f"Erro de processamento na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

    raise ErroModelo(
        f"Falha após {max_tentativas} tentativas. Último erro: {ultimo_erro}",
        max_tentativas - 1,
    )
