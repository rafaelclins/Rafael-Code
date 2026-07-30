import json
import logging
import sys
import threading
import time
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


def _log_progress(modelo: str, tentativa: int, total: int, stop: threading.Event) -> None:
    spinner = r"-\|/"
    i = 0
    start = time.monotonic()
    while not stop.wait(timeout=0.2):
        elapsed = int(time.monotonic() - start)
        i = (i + 1) % 4
        msg = f"\r  {spinner[i]} Aguardando {modelo}... ({elapsed}s)"
        print(msg, end="", file=sys.stderr, flush=True)
        if elapsed > 0 and elapsed % 30 == 0:
            logger.info(
                "Aguardando resposta | modelo=%s | tentativa %d/%d | %ds",
                modelo, tentativa, total, elapsed,
            )
    print("\r" + " " * 60 + "\r", end="", file=sys.stderr, flush=True)


def _enviar_e_extrair(
    sessao: requests.Session,
    payload: dict,
    modelo: str,
    tentativa: int,
    total: int,
) -> str:
    stop = threading.Event()
    t = threading.Thread(
        target=_log_progress, args=(modelo, tentativa, total, stop), daemon=True,
    )
    t.start()
    try:
        resp = sessao.post(ZEN_API_URL, json=payload, timeout=(30, 600))
        resp.raise_for_status()
        raw = resp.json()
        if not isinstance(raw, dict):
            raise ValueError(f"Resposta nao e dict: {type(raw).__name__}")
        return _extrair_texto(raw)
    finally:
        stop.set()


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
                sessao, payload, ZEN_MODEL, tentativa + 1, max_tentativas,
            )

            if not texto_resposta:
                logger.warning(
                    "Resposta vazia. Auto-retry com temperature=0.2..."
                )
                payload["temperature"] = 0.2
                texto_resposta = _enviar_e_extrair(
                    sessao, payload, ZEN_MODEL, tentativa + 1, max_tentativas,
                )

            if not texto_resposta:
                raise ValueError("Resposta vazia da API Zen (mesmo apos auto-retry)")

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
                    "API Zen retornou 401 (Nao Autorizado). "
                    "Verifique se a variavel OPENCODE_ZEN_KEY esta definida corretamente.",
                    tentativa,
                )
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except requests.RequestException as e:
            ultimo_erro = f"Erro de requisicao na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except (ValueError, KeyError, IndexError, TypeError) as e:
            ultimo_erro = f"Erro de processamento na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

    raise ErroModelo(
        f"Falha apos {max_tentativas} tentativas. Ultimo erro: {ultimo_erro}",
        max_tentativas - 1,
    )
