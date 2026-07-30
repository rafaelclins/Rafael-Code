import json
import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    OLLAMA_HOST,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    TEMPERATURA_INCREMENTO,
    TEMPERATURA_INICIAL,
    MAX_TENTATIVAS_MODELO,
)
from parser_defensivo import extrair_e_validar_json

logger = logging.getLogger(__name__)


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
    return session


def aquecer_modelo(sessao: requests.Session) -> None:
    url = f"{OLLAMA_HOST}/api/generate"
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": "ok", "keep_alive": OLLAMA_KEEP_ALIVE}
        resp = sessao.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("Modelo aquecido (keep_alive=%s)", OLLAMA_KEEP_ALIVE)
    except Exception as e:
        logger.warning("Falha ao aquecer modelo (nao critico): %s", e)


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

    url = f"{OLLAMA_HOST}/api/chat"
    sessao = criar_sessao()
    ultimo_erro = ""

    for tentativa in range(max_tentativas):
        temp_atual = temperatura + (tentativa * TEMPERATURA_INCREMENTO)
        logger.debug(
            "Tentativa %d/%d | temp=%.2f | modelo=%s",
            tentativa + 1, max_tentativas, temp_atual, OLLAMA_MODEL,
        )

        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Dados de Entrada:\n{entrada_usuario}"},
                ],
                "stream": False,
                "options": {"temperature": temp_atual},
                "format": esquema_pydantic.model_json_schema(),
            }

            resp = sessao.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            resp.raise_for_status()
            texto_resposta = resp.json()["message"]["content"]

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
                raise ErroModelo(f"Ollama retornou {status}. Verifique se o modelo '{OLLAMA_MODEL}' existe. Detalhe: {e}", tentativa)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except requests.RequestException as e:
            ultimo_erro = f"Erro de requisicao na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

        except ValueError as e:
            ultimo_erro = f"Erro de validacao na tentativa {tentativa + 1}: {e}"
            logger.warning(ultimo_erro)
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)

    raise ErroModelo(
        f"Falha apos {max_tentativas} tentativas. Ultimo erro: {ultimo_erro}",
        max_tentativas - 1,
    )
