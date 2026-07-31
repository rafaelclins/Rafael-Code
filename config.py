import os

ZEN_API_KEY = os.getenv("OPENCODE_ZEN_KEY", "")
ZEN_API_URL = os.getenv("ZEN_API_URL", "https://opencode.ai/zen/v1/responses")
ZEN_MODEL = os.getenv("ZEN_MODEL", "big-pickle")
ZEN_TIMEOUT = int(os.getenv("ZEN_TIMEOUT", "600"))

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder")
OLLAMA_FALLBACK_ATIVADO = os.getenv(
    "OLLAMA_FALLBACK_ATIVADO", "1"
).lower() in ("1", "true", "sim", "yes", "on")

MAX_TENTATIVAS_MODELO = int(os.getenv("MAX_TENTATIVAS_MODELO", "3"))
MAX_REPROVACAO_QUALIDADE = int(os.getenv("MAX_REPROVACAO_QUALIDADE", "3"))
MAX_REPROVACAO_SEGURANCA = int(os.getenv("MAX_REPROVACAO_SEGURANCA", "2"))

TEMPERATURA_INICIAL = float(os.getenv("TEMPERATURA_INICIAL", "0.1"))
TEMPERATURA_INCREMENTO = float(os.getenv("TEMPERATURA_INCREMENTO", "0.2"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

APP_VERSION = "1.2.0"
